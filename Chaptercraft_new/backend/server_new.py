from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import uuid

# Import models and services
from models import *
from database import database, get_database
from sql_models import User as UserDB, BookProject as BookProjectDB, GeneratedBook as GeneratedBookDB
from services.ai_service import AIService
from services.audio_service import AudioService
from services.image_service import ImageService
from services.translation_service import TranslationService
from services.file_service import FileService

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize services
ai_service = AIService()
audio_service = AudioService()
image_service = ImageService()
translation_service = TranslationService()
file_service = FileService()

# Create FastAPI app
app = FastAPI(
    title="Manuscriptify API",
    description="AI-powered audiobook and ebook generation platform",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allow all origins for Replit environment
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads and generated content
uploads_dir = Path("/tmp/uploads")
audio_dir = Path("/tmp/audio_output")
uploads_dir.mkdir(exist_ok=True)
audio_dir.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")
app.mount("/audio", StaticFiles(directory=str(audio_dir)), name="audio")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for progress tracking (in production, use Redis or similar)
progress_store = {}

# Helper function to update progress
async def update_progress(project_id: str, step: str, progress: int, message: str):
    """Update project progress"""
    if project_id not in progress_store:
        progress_store[project_id] = {
            "overall_progress": 0,
            "current_step": step,
            "steps": [],
            "estimated_completion": None
        }
    
    progress_store[project_id]["overall_progress"] = progress
    progress_store[project_id]["current_step"] = step
    progress_store[project_id]["steps"].append({
        "step_name": step,
        "status": "completed" if progress == 100 else "in_progress",
        "progress": progress,
        "message": message,
        "timestamp": datetime.utcnow()
    })

# ============================================================================
# AUTH ENDPOINTS (Simplified for MVP)
# ============================================================================

@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate, db = Depends(get_database)):
    """Register a new user"""
    try:
        # Check if user already exists
        query = "SELECT * FROM users WHERE email = :email"
        existing_user = await db.fetch_one(query=query, values={"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        user_id = str(uuid.uuid4())
        query = """
        INSERT INTO users (id, email, full_name, is_active, subscription_tier, created_at)
        VALUES (:id, :email, :full_name, :is_active, :subscription_tier, :created_at)
        """
        values = {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "is_active": True,
            "subscription_tier": "free",
            "created_at": datetime.utcnow()
        }
        await db.execute(query=query, values=values)
        
        return User(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login")
async def login_user(email: str, password: str, db = Depends(get_database)):
    """Login user (simplified for MVP)"""
    try:
        query = "SELECT * FROM users WHERE email = :email"
        user = await db.fetch_one(query=query, values={"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # In production, verify password hash
        return {
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "subscription_tier": user["subscription_tier"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

@api_router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process document file"""
    try:
        # Read file content
        file_content = await file.read()
        
        # Save and process file
        result = await file_service.save_uploaded_file(
            file_content=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result['error'])
        
        return FileUploadResponse(
            filename=result['filename'],
            file_size=result['file_size'],
            content_type=result['content_type'],
            extracted_text=result['extracted_text'],
            word_count=result['word_count']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@api_router.get("/files/supported-types")
async def get_supported_file_types():
    """Get supported file types"""
    return file_service.get_supported_types()

# ============================================================================
# BOOK PROJECT ENDPOINTS  
# ============================================================================

@api_router.post("/projects", response_model=BookProject)
async def create_project(project_data: BookProjectCreate, user_id: str, db = Depends(get_database)):
    """Create a new book project"""
    try:
        project_id = str(uuid.uuid4())
        query = """
        INSERT INTO projects (id, user_id, title, author, description, settings, content, created_at, updated_at)
        VALUES (:id, :user_id, :title, :author, :description, :settings, :content, :created_at, :updated_at)
        """
        values = {
            "id": project_id,
            "user_id": user_id,
            "title": project_data.title,
            "author": project_data.author,
            "description": project_data.description,
            "settings": project_data.settings.dict(),
            "content": project_data.content,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.execute(query=query, values=values)
        
        return BookProject(
            id=project_id,
            user_id=user_id,
            title=project_data.title,
            author=project_data.author,
            description=project_data.description,
            settings=project_data.settings,
            content=project_data.content
        )
        
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@api_router.get("/projects/{user_id}", response_model=List[BookProject])
async def get_user_projects(user_id: str, db = Depends(get_database)):
    """Get all projects for a user"""
    try:
        query = "SELECT * FROM projects WHERE user_id = :user_id ORDER BY created_at DESC LIMIT 100"
        projects = await db.fetch_all(query=query, values={"user_id": user_id})
        
        result = []
        for project in projects:
            result.append(BookProject(
                id=project["id"],
                user_id=project["user_id"],
                title=project["title"],
                author=project["author"],
                description=project["description"],
                settings=BookSettings(**project["settings"]) if project["settings"] else None,
                status=ProductionStatus(project["status"]),
                content=project["content"],
                generated_content=project["generated_content"] or "",
                cover_image_url=project["cover_image_url"],
                audio_file_url=project["audio_file_url"],
                created_at=project["created_at"],
                updated_at=project["updated_at"],
                progress=project["progress"],
                processing_logs=project["processing_logs"] or []
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "ai_service": "configured",
            "audio_service": "configured",
            "image_service": "configured",
            "translation_service": "configured",
            "file_service": "configured"
        }
    }

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Manuscriptify API is running", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    await database.connect()
    logger.info("Database connected")

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    logger.info("Database disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
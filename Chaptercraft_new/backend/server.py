from fastapi import FastAPI, APIRouter, HTTPException, File, UploadFile, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorClient
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
from services.ai_service import AIService
from services.audio_service import AudioService
from services.image_service import ImageService
from services.translation_service import TranslationService
from services.file_service import FileService

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads and generated content
if not os.path.exists('/app/uploads'):
    os.makedirs('/app/uploads')
if not os.path.exists('/app/audio_output'):
    os.makedirs('/app/audio_output')

app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")
app.mount("/audio", StaticFiles(directory="/app/audio_output"), name="audio")

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
async def register_user(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user (in production, hash the password)
        user = User(
            email=user_data.email,
            full_name=user_data.full_name
        )
        
        await db.users.insert_one(user.dict())
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login")
async def login_user(email: str, password: str):
    """Login user (simplified for MVP)"""
    try:
        user = await db.users.find_one({"email": email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # In production, verify password hash
        return {
            "user_id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "subscription_tier": user.get("subscription_tier", "free")
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
async def create_project(project_data: BookProjectCreate, user_id: str):
    """Create a new book project"""
    try:
        project = BookProject(
            user_id=user_id,
            title=project_data.title,
            author=project_data.author,
            description=project_data.description,
            settings=project_data.settings,
            content=project_data.content
        )
        
        await db.projects.insert_one(project.dict())
        return project
        
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")

@api_router.get("/projects/{user_id}", response_model=List[BookProject])
async def get_user_projects(user_id: str):
    """Get all projects for a user"""
    try:
        projects = await db.projects.find({"user_id": user_id}).to_list(100)
        return [BookProject(**project) for project in projects]
        
    except Exception as e:
        logger.error(f"Failed to get projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve projects")

@api_router.get("/projects/detail/{project_id}", response_model=BookProject)
async def get_project(project_id: str):
    """Get specific project details"""
    try:
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return BookProject(**project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve project")

@api_router.put("/projects/{project_id}", response_model=BookProject)
async def update_project(project_id: str, updates: BookProjectUpdate):
    """Update project details"""
    try:
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        update_data['updated_at'] = datetime.utcnow()
        
        result = await db.projects.update_one(
            {"id": project_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        updated_project = await db.projects.find_one({"id": project_id})
        return BookProject(**updated_project)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")

# ============================================================================
# AI GENERATION ENDPOINTS
# ============================================================================

@api_router.post("/ai/generate-book")
async def generate_book_from_prompt(request: PromptToBookRequest, background_tasks: BackgroundTasks):
    """Generate a complete book from a prompt"""
    try:
        project_id = str(uuid.uuid4())
        
        # Start background task for book generation
        background_tasks.add_task(
            generate_book_background,
            project_id,
            request.prompt,
            request.genre.value,
            request.length,
            request.target_language.value
        )
        
        return {
            "project_id": project_id,
            "message": "Book generation started",
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Book generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start book generation")

async def generate_book_background(project_id: str, prompt: str, genre: str, length: str, language: str):
    """Background task for book generation"""
    try:
        await update_progress(project_id, "Generating content", 10, "Starting AI content generation")
        
        # Generate book content
        content = await ai_service.generate_book_from_prompt(prompt, genre, length)
        
        await update_progress(project_id, "Content generated", 50, "Book content generated successfully")
        
        # Save to database (simplified)
        project_data = {
            "id": project_id,
            "title": f"Generated {genre.title()}",
            "content": content,
            "status": "completed",
            "generated_at": datetime.utcnow()
        }
        
        await db.generated_books.insert_one(project_data)
        
        await update_progress(project_id, "Completed", 100, "Book generation completed")
        
    except Exception as e:
        logger.error(f"Background book generation failed: {e}")
        await update_progress(project_id, "Failed", 0, f"Generation failed: {str(e)}")

@api_router.post("/ai/generate-titles")
async def generate_titles(request: TitleGenerationRequest):
    """Generate title suggestions"""
    try:
        titles = await ai_service.generate_title_suggestions(
            content_sample=request.content_sample,
            genre=request.genre.value,
            count=5
        )
        
        return {"titles": titles}
        
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate titles")

@api_router.post("/ai/generate-outline")
async def generate_chapter_outline(request: ChapterOutlineRequest):
    """Generate chapter outline"""
    try:
        outline = await ai_service.generate_chapter_outline(
            title=request.title,
            genre=request.genre.value,
            content_summary=request.content_summary,
            num_chapters=request.num_chapters
        )
        
        return {"outline": outline}
        
    except Exception as e:
        logger.error(f"Outline generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate outline")

# ============================================================================
# AUDIO GENERATION ENDPOINTS
# ============================================================================

@api_router.post("/audio/generate", response_model=AudioGenerationResponse)
async def generate_audio(request: AudioGenerationRequest, background_tasks: BackgroundTasks):
    """Generate audio from text"""
    try:
        result = await audio_service.generate_audio(
            text=request.text,
            language=request.language.value,
            voice_style=request.voice_style,
            speed=request.speed
        )
        
        return AudioGenerationResponse(
            audio_url=result['audio_url'],
            duration=result['duration'],
            file_size=result['file_size']
        )
        
    except Exception as e:
        logger.error(f"Audio generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate audio")

@api_router.post("/audio/generate-audiobook/{project_id}")
async def generate_audiobook(project_id: str, voice_style: str = "narrator", speed: float = 1.0, background_tasks: BackgroundTasks = None):
    """Generate complete audiobook for a project"""
    try:
        # Get project content
        project = await db.projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Start background audiobook generation
        background_tasks.add_task(
            generate_audiobook_background,
            project_id,
            project['content'],
            voice_style,
            speed
        )
        
        return {
            "message": "Audiobook generation started",
            "project_id": project_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Audiobook generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to start audiobook generation")

async def generate_audiobook_background(project_id: str, content: str, voice_style: str, speed: float):
    """Background task for audiobook generation"""
    try:
        # Progress callback
        async def progress_callback(message: str, progress: int):
            await update_progress(project_id, "Generating audiobook", progress, message)
        
        result = await audio_service.generate_audiobook(
            project_id=project_id,
            content=content,
            voice_style=voice_style,
            speed=speed,
            progress_callback=progress_callback
        )
        
        # Update project with audiobook URL
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {
                "audio_file_url": result['audiobook_url'],
                "status": "completed",
                "updated_at": datetime.utcnow()
            }}
        )
        
        await update_progress(project_id, "Completed", 100, "Audiobook generation completed")
        
    except Exception as e:
        logger.error(f"Background audiobook generation failed: {e}")
        await update_progress(project_id, "Failed", 0, f"Audiobook generation failed: {str(e)}")

@api_router.get("/audio/voices")
async def get_available_voices(language: Optional[str] = None):
    """Get available voice models"""
    return await audio_service.get_available_voices(language)

# ============================================================================
# IMAGE GENERATION ENDPOINTS
# ============================================================================

@api_router.post("/images/generate-cover")
async def generate_cover_art(request: CoverArtRequest):
    """Generate book cover art"""
    try:
        result = await image_service.generate_cover_art(
            title=request.title,
            genre=request.genre.value,
            description=request.description,
            style=request.style
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Cover art generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate cover art")

@api_router.get("/images/styles/{genre}")
async def get_genre_styles(genre: BookGenre):
    """Get available art styles for a genre"""
    return await image_service.get_genre_styles(genre.value)

# ============================================================================
# TRANSLATION ENDPOINTS
# ============================================================================

@api_router.post("/translate/text", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text to target language"""
    try:
        result = await translation_service.translate_text(
            text=request.text,
            target_language=request.target_language.value,
            source_language=request.source_language.value if request.source_language else None
        )
        
        return TranslationResponse(
            original_text=result['original_text'],
            translated_text=result['translated_text'],
            source_language=result['source_language'],
            target_language=result['target_language'],
            confidence=result['confidence']
        )
        
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        raise HTTPException(status_code=500, detail="Translation failed")

@api_router.get("/translate/languages")
async def get_supported_languages():
    """Get supported languages for translation"""
    return translation_service.get_supported_languages()

# ============================================================================
# PROGRESS TRACKING ENDPOINTS
# ============================================================================

@api_router.get("/progress/{project_id}", response_model=ProjectProgress)
async def get_project_progress(project_id: str):
    """Get project processing progress"""
    try:
        if project_id not in progress_store:
            raise HTTPException(status_code=404, detail="Progress not found")
        
        progress_data = progress_store[project_id]
        
        return ProjectProgress(
            project_id=project_id,
            overall_progress=progress_data["overall_progress"],
            current_step=progress_data["current_step"],
            steps=[ProcessingStep(**step) for step in progress_data["steps"]],
            estimated_completion=progress_data.get("estimated_completion")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get progress: {e}")
        raise HTTPException(status_code=500, detail="Failed to get progress")

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        # Get counts from database
        total_users = await db.users.count_documents({})
        total_projects = await db.projects.count_documents({})
        active_projects = await db.projects.count_documents({"status": "processing"})
        completed_projects = await db.projects.count_documents({"status": "completed"})
        
        # Get popular genres
        pipeline = [
            {"$group": {"_id": "$settings.genre", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        genre_stats = await db.projects.aggregate(pipeline).to_list(10)
        popular_genres = {item["_id"]: item["count"] for item in genre_stats}
        
        return AdminStats(
            total_users=total_users,
            total_projects=total_projects,
            active_projects=active_projects,
            completed_projects=completed_projects,
            revenue=0.0,  # Would come from payment system
            popular_genres=popular_genres
        )
        
    except Exception as e:
        logger.error(f"Failed to get admin stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "ai_service": "configured",
            "audio_service": "configured",
            "image_service": "configured" if image_service.is_configured() else "not_configured",
            "translation_service": "configured" if translation_service.is_configured() else "not_configured",
            "file_service": "configured"
        }
    }

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Manuscriptify API is running", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
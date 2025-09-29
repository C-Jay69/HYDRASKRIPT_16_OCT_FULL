from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any
from datetime import datetime
import uuid

# Load environment variables  
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Create FastAPI app
app = FastAPI(
    title="Manuscriptify API",
    description="AI-powered audiobook and ebook generation platform",
    version="1.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# CORS middleware - Allow all origins for Replit environment
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Allow all origins for Replit proxy
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Manuscriptify API is running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@api_router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Manuscriptify API is running", "version": "1.0.0"}

# Mock data endpoints for frontend testing
@api_router.get("/projects/{user_id}")
async def get_user_projects(user_id: str):
    """Get user projects (mock data)"""
    return [
        {
            "id": str(uuid.uuid4()),
            "title": "Sample Book Project",
            "author": "Demo Author",
            "status": "completed",
            "created_at": datetime.utcnow().isoformat(),
            "progress": 100
        }
    ]

@api_router.post("/auth/login")
async def login_user(email: str, password: str):
    """Login user (mock authentication)"""
    return {
        "user_id": str(uuid.uuid4()),
        "email": email,
        "full_name": "Demo User",
        "subscription_tier": "free"
    }

@api_router.get("/files/supported-types")
async def get_supported_file_types():
    """Get supported file types"""
    return {
        "mime_types": ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        "extensions": [".txt", ".pdf", ".docx"],
        "max_file_size_mb": 25,
        "description": "Supported formats: TXT, PDF, DOCX"
    }

# Include the router in the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
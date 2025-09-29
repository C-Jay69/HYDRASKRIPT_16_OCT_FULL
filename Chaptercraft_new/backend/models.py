from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid

class BookGenre(str, Enum):
    EBOOK = "ebook"
    NOVEL = "novel"
    KIDS_STORY = "kids_story"
    COLORING_BOOK = "coloring_book"
    AUDIOBOOK = "audiobook"

class ProductionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SupportedLanguage(str, Enum):
    ENGLISH = "en"
    FRENCH = "fr"
    SPANISH = "es"
    MANDARIN = "zh"
    HINDI = "hi"
    JAPANESE = "ja"

# User Models
class UserBase(BaseModel):
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    subscription_tier: str = "free"
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Book Project Models
class BookSettings(BaseModel):
    genre: BookGenre
    target_language: SupportedLanguage = SupportedLanguage.ENGLISH
    page_size: str  # "6x9" or "8x10"
    max_pages: int
    min_pages: Optional[int] = None
    include_images: bool = False
    voice_style: str = "neutral"
    chapter_structure: bool = True

class BookProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    author: str = ""
    description: str = ""
    settings: BookSettings
    status: ProductionStatus = ProductionStatus.PENDING
    content: str = ""
    generated_content: str = ""
    cover_image_url: Optional[str] = None
    audio_file_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    progress: int = 0  # 0-100
    processing_logs: List[str] = []

class BookProjectCreate(BaseModel):
    title: str
    description: str = ""
    settings: BookSettings
    content: str = ""
    author: str = ""

class BookProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    author: Optional[str] = None

# AI Generation Models
class PromptToBookRequest(BaseModel):
    prompt: str
    genre: BookGenre
    target_language: SupportedLanguage = SupportedLanguage.ENGLISH
    length: str = "medium"  # short, medium, long
    style: str = "engaging"

class TitleGenerationRequest(BaseModel):
    content_sample: str
    genre: BookGenre
    style: str = "engaging"

class ChapterOutlineRequest(BaseModel):
    title: str
    genre: BookGenre
    content_summary: str
    num_chapters: int = 10

class CoverArtRequest(BaseModel):
    title: str
    genre: BookGenre
    description: str
    style: str = "professional"  # professional, artistic, children, minimalist

# Audio Generation Models
class AudioGenerationRequest(BaseModel):
    text: str
    voice_style: str = "neutral"
    language: SupportedLanguage = SupportedLanguage.ENGLISH
    speed: float = 1.0

class AudioGenerationResponse(BaseModel):
    audio_url: str
    duration: float
    file_size: int

# Translation Models
class TranslationRequest(BaseModel):
    text: str
    target_language: SupportedLanguage
    source_language: Optional[SupportedLanguage] = None
    preserve_formatting: bool = True

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float

# File Upload Models
class FileUploadResponse(BaseModel):
    filename: str
    file_size: int
    content_type: str
    extracted_text: str
    word_count: int

# Payment Models
class SubscriptionTier(BaseModel):
    name: str
    price: float
    features: List[str]
    max_projects: int
    max_file_size_mb: int

class PaymentIntent(BaseModel):
    amount: int
    currency: str = "usd"
    tier: str

# Progress Tracking
class ProcessingStep(BaseModel):
    step_name: str
    status: str
    progress: int
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProjectProgress(BaseModel):
    project_id: str
    overall_progress: int
    current_step: str
    steps: List[ProcessingStep]
    estimated_completion: Optional[datetime] = None

# Admin Models
class AdminStats(BaseModel):
    total_users: int
    total_projects: int
    active_projects: int
    completed_projects: int
    revenue: float
    popular_genres: Dict[str, int]
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="free")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to projects
    projects = relationship("BookProject", back_populates="user")

class BookProject(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, default="")
    description = Column(Text, default="")
    settings = Column(JSON)  # Store BookSettings as JSON
    status = Column(String, default="pending")  # pending, processing, completed, failed
    content = Column(Text, default="")
    generated_content = Column(Text, default="")
    cover_image_url = Column(String, nullable=True)
    audio_file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    progress = Column(Integer, default=0)  # 0-100
    processing_logs = Column(JSON, default=list)  # Store list of logs
    
    # Relationship to user
    user = relationship("User", back_populates="projects")

class GeneratedBook(Base):
    __tablename__ = "generated_books"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(Text)
    status = Column(String, default="completed")
    generated_at = Column(DateTime, default=datetime.utcnow)

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_size = Column(Integer)
    content_type = Column(String)
    extracted_text = Column(Text)
    word_count = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
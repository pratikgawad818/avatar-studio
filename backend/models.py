"""
Avatar Studio - Database Models
SQLAlchemy ORM models for users, projects, jobs, assets
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime
import uuid
from enum import Enum as PyEnum


class JobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssetType(str, PyEnum):
    AVATAR = "avatar"
    VOICE = "voice"
    BACKGROUND = "background"


class User(Base):
    """User model for authentication and project ownership"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="owner", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Project(Base):
    """Project model for organizing videos and assets"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    thumbnail_url = Column(String(512))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    jobs = relationship("Job", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.name}>"


class Asset(Base):
    """Asset model for avatars, voices, backgrounds"""
    __tablename__ = "assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    asset_type = Column(Enum(AssetType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_mb = Column(Float)
    thumbnail_url = Column(String(512))
    metadata = Column(Text)  # JSON string
    duration_seconds = Column(Float)  # For audio/video
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="assets")

    def __repr__(self):
        return f"<Asset {self.asset_type}:{self.name}>"


class Job(Base):
    """Job model for video generation tracking"""
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    project_id = Column(String(36), ForeignKey("projects.id"))
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    progress = Column(Integer, default=0)  # 0-100
    current_step = Column(String(255))
    error_message = Column(Text)
    output_file_path = Column(String(512))
    output_url = Column(String(512))
    
    # Input parameters (JSON)
    script = Column(Text)
    avatar_id = Column(String(36))
    voice_id = Column(String(36))
    background_id = Column(String(36))
    voice_mode = Column(String(50))  # "fast" or "clone"
    resolution = Column(String(50), default="1920x1080")
    aspect_ratio = Column(String(50), default="16:9")
    
    # Timing
    estimated_duration_seconds = Column(Integer)
    actual_duration_seconds = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="jobs")
    project = relationship("Project", back_populates="jobs")

    def __repr__(self):
        return f"<Job {self.id}:{self.status}>"

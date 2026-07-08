"""
Avatar Studio - Pydantic Schemas
Request/Response validation and serialization
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class JobStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AssetTypeEnum(str, Enum):
    AVATAR = "avatar"
    VOICE = "voice"
    BACKGROUND = "background"


# ───── User Schemas ─────
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ───── Asset Schemas ─────
class AssetResponse(BaseModel):
    id: str
    asset_type: AssetTypeEnum
    name: str
    file_path: str
    file_size_mb: Optional[float]
    thumbnail_url: Optional[str]
    duration_seconds: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int


# ───── Project Schemas ─────
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    is_public: bool = False


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    is_public: bool
    thumbnail_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ───── Job/Generation Schemas ─────
class GenerationRequest(BaseModel):
    project_id: Optional[str] = None
    script: str = Field(..., min_length=1, max_length=5000)
    avatar_id: str
    voice_id: str
    background_id: Optional[str] = None
    voice_mode: str = Field(default="fast", regex="^(fast|clone)$")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0)
    position: str = Field(default="center", regex="^(left|center|right)$")
    avatar_scale: float = Field(default=0.75, ge=0.5, le=1.5)
    resolution: str = Field(default="1920x1080", regex="^\\d+x\\d+$")
    aspect_ratio: str = Field(default="16:9", regex="^\\d+:\\d+$")
    subtitles: bool = True
    sub_style: str = Field(default="netflix", regex="^(netflix|minimal|classic)$")
    whisper_model: str = Field(default="base", regex="^(tiny|base|small|medium|large)$")

    @validator('script')
    def script_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Script cannot be empty')
        return v.strip()


class JobResponse(BaseModel):
    id: str
    status: JobStatusEnum
    progress: int
    current_step: Optional[str]
    error_message: Optional[str]
    output_url: Optional[str]
    estimated_duration_seconds: Optional[int]
    actual_duration_seconds: Optional[int]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


class ProgressUpdate(BaseModel):
    """Real-time progress update (SSE)"""
    job_id: str
    status: JobStatusEnum
    progress: int
    current_step: str
    log: Optional[str]
    error: Optional[str]


# ───── Estimation Schemas ─────
class EstimationRequest(BaseModel):
    script: str = Field(..., min_length=1, max_length=5000)
    voice_mode: str = Field(default="fast", regex="^(fast|clone)$")


class EstimationResponse(BaseModel):
    word_count: int
    estimated_seconds: int
    estimated_minutes: float
    breakdown: dict  # {"voice": int, "lipsync": int, "composite": int}
    warning: Optional[str]

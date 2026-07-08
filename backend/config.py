"""
Avatar Studio - Configuration Management
Environment-aware settings with validation
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # App
    APP_NAME: str = "Avatar Studio"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    RELOAD: bool = False
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./avatar_studio.db")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    
    # JWT & Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Storage
    BASE_DIR: str = Field(default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    AVATARS_DIR: str = Field(default="./data/avatars")
    VOICES_DIR: str = Field(default="./data/voices")
    BACKGROUNDS_DIR: str = Field(default="./data/backgrounds")
    OUTPUTS_DIR: str = Field(default="./data/outputs")
    TEMP_DIR: str = Field(default="./data/temp")
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 50  # Max 50MB per file
    MAX_VIDEO_DURATION_SECONDS: int = 3600  # Max 1 hour
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2")
    
    # AI Models
    WHISPER_MODEL: str = "base"
    F5TTS_MODEL_DIR: str = Field(default="./models/F5-TTS")
    WAV2LIP_CHECKPOINT: str = Field(default="./models/Wav2Lip/checkpoints/wav2lip_gan.pth")
    
    # Feature flags
    ENABLE_VOICE_CLONING: bool = True
    ENABLE_BATCH_PROCESSING: bool = True
    ENABLE_BACKGROUND_REMOVAL: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

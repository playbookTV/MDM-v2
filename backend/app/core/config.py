"""
Application configuration using Pydantic Settings
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Basic app settings
    APP_NAME: str = "Modomo Dataset Management API"
    VERSION: str = "1.0.0"
    PORT: int = Field(default=8000, description="Port to run the server on")
    PRODUCTION: bool = Field(default=False, description="Production mode flag")
    
    # Database settings
    DATABASE_URL: str = Field(..., description="Supabase/PostgreSQL connection string")
    DATABASE_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    
    # Supabase settings
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_ANON_KEY: str = Field(..., description="Supabase anon key")
    SUPABASE_SECRET_KEY: str = Field(..., description="Supabase service role key")
    
    # Redis settings (for job queue)
    REDIS_URL: str = Field(..., description="Redis connection string")
    REDIS_JOB_QUEUE: str = Field(default="modomo:jobs:queue", description="Redis queue name for jobs")
    REDIS_EVENT_STREAM: str = Field(default="modomo:jobs:events", description="Redis stream for job events")
    
    # Cloudflare R2 settings
    R2_ACCOUNT_ID: str = Field(..., description="Cloudflare R2 account ID")
    R2_ACCESS_KEY_ID: str = Field(..., description="Cloudflare R2 access key")
    R2_SECRET_ACCESS_KEY: str = Field(..., description="Cloudflare R2 secret key")
    R2_BUCKET_NAME: str = Field(default="modomo-datasets", description="R2 bucket name")
    R2_ENDPOINT_URL: str = Field(..., description="R2 endpoint URL")
    R2_PUBLIC_URL: str = Field(..., description="R2 public URL base")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"], 
        description="Allowed CORS origins"
    )
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default pagination page size")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum pagination page size")
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = Field(default=50 * 1024 * 1024, description="Max file upload size (50MB)")
    ALLOWED_IMAGE_TYPES: List[str] = Field(
        default=["image/jpeg", "image/png", "image/webp"],
        description="Allowed image MIME types"
    )
    
    # Presigned URL settings
    PRESIGNED_URL_EXPIRES: int = Field(default=900, description="Presigned URL expiration in seconds (15 minutes)")
    
    # Job processing settings  
    JOB_TIMEOUT: int = Field(default=1800, description="Job timeout in seconds (30 minutes)")
    JOB_RETRY_ATTEMPTS: int = Field(default=3, description="Max job retry attempts")
    
    # Celery worker settings
    CELERY_WORKER_CONCURRENCY: int = Field(default=2, description="Celery worker concurrency")
    CELERY_WORKER_MAX_TASKS: int = Field(default=100, description="Max tasks per worker child process")
    CELERY_RESULT_EXPIRES: int = Field(default=3600, description="Celery result expiration in seconds")
    
    # RunPod AI processing settings
    RUNPOD_API_KEY: Optional[str] = Field(default=None, description="RunPod API key for serverless AI")
    RUNPOD_ENDPOINT_ID: Optional[str] = Field(default=None, description="RunPod serverless endpoint ID")
    RUNPOD_ENDPOINT_URL: Optional[str] = Field(default=None, description="RunPod custom endpoint URL")
    RUNPOD_TIMEOUT: int = Field(default=300, description="RunPod request timeout in seconds (5 minutes)")
    RUNPOD_MAX_RETRIES: int = Field(default=2, description="Max RunPod API retries")
    
    # AI processing fallback settings
    USE_LOCAL_AI: bool = Field(default=True, description="Use local AI models when RunPod unavailable")
    AI_PROCESSING_ENABLED: bool = Field(default=True, description="Enable real AI processing (vs mocks)")
    AI_MODEL_CACHE_DIR: str = Field(default="./models", description="Directory for local AI model cache")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

# Create global settings instance
settings = Settings()

# Environment-specific configurations
if settings.PRODUCTION:
    # Production specific settings
    settings.CORS_ORIGINS = [
        "https://modomo-app.railway.app",
        "https://modomo.app"  # Add your production domains
    ]
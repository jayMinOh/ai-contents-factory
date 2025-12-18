from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AI Video Marketing Platform"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database (MariaDB)
    DATABASE_URL: str = "mysql+aiomysql://aivm:aivm_dev_password@localhost:3306/ai_video_marketing"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Google Gemini
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"  # 또는 gemini-2.5-pro, gemini-3.0-pro

    # OpenAI (Whisper용, 선택사항)
    OPENAI_API_KEY: Optional[str] = None

    # Storage (MinIO/S3)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ai-video-marketing"

    # Video Generation APIs
    LUMA_API_KEY: Optional[str] = None
    RUNWAY_API_KEY: Optional[str] = None
    HEYGEN_API_KEY: Optional[str] = None

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Paths
    TEMP_DIR: str = "storage"  # Persistent storage (relative to backend/)
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

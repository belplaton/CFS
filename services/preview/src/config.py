"""
Configuration settings for Preview Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    env: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://cloudstorage:cloudstorage_secret@postgres-preview:5432/cloudstorage_preview"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin_secret"
    minio_secure: bool = False

    # Preview settings
    preview_cache_ttl: int = 3600  # 1 hour
    thumbnail_size: tuple = (256, 256)
    preview_max_size: int = 10485760  # 10 MB

    # Service-to-service auth
    service_api_key: str = "change-this-in-production"
    
    # Inter-service URLs
    file_service_url: str = "http://file:8000"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

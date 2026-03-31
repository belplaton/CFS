"""
Configuration settings for File Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    env: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://cloudstorage:cloudstorage_secret@postgres-file:5432/cloudstorage_file"

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin_secret"
    minio_bucket: str = "cloudstorage"
    minio_secure: bool = False

    # Storage quotas (bytes)
    default_storage_quota: int = 5368709120  # 5 GB
    premium_storage_quota: int = 107374182400  # 100 GB

    # Service-to-service auth
    service_api_key: str = "change-this-in-production"
    
    # Inter-service URLs
    auth_service_url: str = "http://auth:8000"
    
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

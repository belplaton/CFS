"""
Configuration settings for Auth Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""

    # Application
    env: str = "development"

    # Database (No default for security)
    database_url: str  # Must be set via env or .env file

    # JWT (No default for security)
    jwt_secret: str  # Must be set via env
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth Google
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # Email (SMTP)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@cloudstorage.local"

    # Frontend
    frontend_url: str = "http://localhost:8080"

    # Service-to-service auth
    service_api_key: str  # Must be set via env

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

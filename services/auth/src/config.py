"""
Configuration settings for Auth Service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # Application
    env: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://cloudstorage:cloudstorage_secret@postgres-auth:5432/cloudstorage_auth"

    # JWT
    jwt_secret: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # OAuth Google
    google_client_id: str = ""
    google_client_secret: str = ""

    # Email (SMTP)
    smtp_host: str = "smtp.mailtrap.io"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@cloudstorage.local"

    # Frontend
    frontend_url: str = "http://localhost:8080"

    # Service-to-service auth
    service_api_key: str = "change-this-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

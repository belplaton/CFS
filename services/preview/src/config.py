"""
Configuration settings for Preview Service
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    env: str = "development"

    file_service_url: str = "http://file:8000"
    service_api_key: str = ""

    preview_max_size: int = 10485760  # 10 MB
    preview_cache_ttl: int = 3600  # reserved for future caching

    cors_origins: list[str] = ["http://localhost:8080"]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

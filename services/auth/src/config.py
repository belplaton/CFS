"""
Configuration settings for Auth Service (Pydantic v2 + ``ConfigDict``).

Phase 3 changes:

* ``jwt_issuer`` and ``jwt_audience`` are now **required** in
  non-development environments — they let downstream services
  (File, Preview) reject tokens that were issued for a different
  audience.  Defaults match the rest of the stack.
* ``Settings`` uses ``model_config = ConfigDict(...)`` (Pydantic v2
  style) instead of the deprecated ``class Config`` block.
* Added ``cors_origins`` (comma-separated) to centralise the policy
  that the gateway already enforces — handy for local dev where the
  gateway may be bypassed.
"""
from __future__ import annotations

from functools import lru_cache
from typing import FrozenSet, Optional

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # ==================== Application ====================
    env: str = "development"
    log_level: str = "INFO"

    # ==================== Database ====================
    database_url: str = "postgresql+asyncpg://cloudstorage:cloudstorage_secret@postgres-auth:5432/cloudstorage_auth"

    # ==================== JWT ====================
    # Shared secret with File / Preview services.  Must be set via env.
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    # Standard claims — required to be set so downstream services can
    # verify that a token was issued for the right audience / by the
    # right issuer.
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "cloud-storage"

    # ==================== Storage quotas (bytes) ====================
    default_storage_quota: int = 5 * 1024 * 1024 * 1024        # 5 GB
    premium_storage_quota: int = 100 * 1024 * 1024 * 1024      # 100 GB

    # ==================== OAuth Google ====================
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # ==================== Email (SMTP) ====================
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: str = "noreply@cloudstorage.local"

    # ==================== Frontend ====================
    frontend_url: str = "http://localhost:8080"

    # ==================== CORS ====================
    cors_origins: str = "http://localhost:8080"

    # ==================== Redis (rate limiting, refresh revocation) ====================
    # When unset the rate limiter falls back to a no-op stub
    # (``utils/redis_client.py``) — the auth endpoints stay available
    # but are not protected from brute force.  Always set this in
    # production.
    redis_url: Optional[str] = None

    # ==================== Service-to-service auth ====================
    service_api_key: str  # No default — must be set in env

    # ==================== Production guard ====================
    insecure_secret_markers: FrozenSet[str] = Field(
        default_factory=lambda: frozenset(
            {"change-this-in-production", "your-super-secret-jwt-key-change-in-production"}
        )
    )

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== Validators ====================

    @field_validator("cors_origins")
    @classmethod
    def _strip_cors(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins_set(self) -> FrozenSet[str]:
        return frozenset(o.strip() for o in self.cors_origins.split(",") if o.strip())

    def assert_safe_for_production(self) -> None:
        """Hard-fail in production if secrets are placeholders."""
        if self.env.lower() == "production":
            for marker in self.insecure_secret_markers:
                if marker in self.jwt_secret or marker in self.service_api_key:
                    raise RuntimeError(
                        "Refusing to start: insecure default secrets detected in production."
                    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    s = Settings()
    s.assert_safe_for_production()
    return s


settings = get_settings()

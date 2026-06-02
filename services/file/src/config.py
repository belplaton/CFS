"""
Configuration settings for File Service
"""
from datetime import timedelta
from functools import lru_cache
from typing import FrozenSet

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # ==================== Application ====================
    env: str = "development"
    log_level: str = "INFO"

    # ==================== Database ====================
    database_url: str = "postgresql+asyncpg://cloudstorage:cloudstorage_secret@postgres-file:5432/cloudstorage_file"

    # ==================== MinIO ====================
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin_secret"
    minio_bucket: str = "cloudstorage"
    minio_secure: bool = False

    # MinIO object key prefixes (per user_id)
    minio_prefix_files: str = "files"
    minio_prefix_trash: str = "trash"

    # ==================== Storage quotas (bytes) ====================
    default_storage_quota: int = 5 * 1024 * 1024 * 1024          # 5 GB
    premium_storage_quota: int = 100 * 1024 * 1024 * 1024        # 100 GB

    # ==================== Upload limits (Phase 1: security) ====================
    # Hard cap for a single uploaded object.
    max_upload_size: int = 100 * 1024 * 1024                     # 100 MB (per ROADMAP)
    # Streaming buffer size when reading UploadFile.
    stream_chunk_size: int = 1024 * 1024                         # 1 MB
    # Filename length cap (matches DB column).
    max_filename_length: int = 255

    # ==================== Upload policy: whitelist ====================
    # Comma-separated envs, parsed into a frozenset.
    # Defaults are a safe MVP whitelist (see ARCHITECTURE / ROADMAP).
    allowed_mime_types: str = (
        "image/jpeg,image/png,image/gif,image/webp,image/svg+xml,"
        "application/pdf,text/plain,text/csv,application/json,"
        "application/msword,"
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document,"
        "application/vnd.ms-excel,"
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,"
        "application/vnd.ms-powerpoint,"
        "application/vnd.openxmlformats-officedocument.presentationml.presentation,"
        "application/zip,application/x-tar,application/gzip"
    )
    allowed_extensions: str = (
        "jpg,jpeg,png,gif,webp,svg,"
        "pdf,txt,csv,json,"
        "doc,docx,xls,xlsx,ppt,pptx,"
        "zip,tar,gz"
    )

    # ==================== JWT (shared with Auth Service) ====================
    jwt_secret: str  # No default — must be set in env
    jwt_algorithm: str = "HS256"
    # iss / aud claims must match the values the Auth service stamps
    # onto its tokens.  Defaults match the cross-service contract.
    jwt_issuer: str = "auth-service"
    jwt_audience: str = "cloud-storage"

    # ==================== Presigned URLs (Phase 1: tightened) ====================
    # Short-lived URLs for direct MinIO access. Used only by internal flows.
    presigned_url_expires_seconds: int = 15 * 60                 # 15 minutes
    presigned_url_expires: timedelta = Field(
        default_factory=lambda: timedelta(seconds=15 * 60)
    )

    # ==================== Frontend ====================
    frontend_url: str = "http://localhost:8080"

    # ==================== Service-to-service auth ====================
    service_api_key: str  # No default — must be set in env

    # ==================== Inter-service URLs ====================
    auth_service_url: str = "http://auth:8000"

    # ==================== Redis ====================
    redis_url: str = "redis://redis:6379/0"

    # ==================== Production guard ====================
    # Refuse to start in production with placeholder secrets.
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

    @field_validator("allowed_mime_types", "allowed_extensions")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def allowed_mime_set(self) -> FrozenSet[str]:
        return frozenset(
            m.strip().lower() for m in self.allowed_mime_types.split(",") if m.strip()
        )

    @property
    def allowed_ext_set(self) -> FrozenSet[str]:
        return frozenset(
            e.strip().lower().lstrip(".") for e in self.allowed_extensions.split(",") if e.strip()
        )

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
    """Get cached settings instance"""
    s = Settings()
    s.assert_safe_for_production()
    return s


settings = get_settings()

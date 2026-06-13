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
    default_storage_quota: int = 5 * 1024 * 1024 * 1024  # 5 GB
    premium_storage_quota: int = 100 * 1024 * 1024 * 1024  # 100 GB

    # ==================== Trash TTL (Phase 4.2) ====================
    # How long a soft-deleted file lives in trash before the cleanup
    # job hard-deletes it.  30 days matches typical consumer cloud
    # storage retention.
    trash_retention_days: int = 30
    # Cron expression for the cleanup job.  Default = 03:17 every day.
    trash_cleanup_cron: str = "17 3 * * *"
    # Master switch: when ``False`` the scheduler is still built but
    # no jobs are registered.  Useful for unit tests and one-off
    # containers that should not run a background tick.
    trash_cleanup_enabled: bool = True

    # ==================== Upload limits (Phase 1: security) ====================
    # Hard cap for a single uploaded object.
    max_upload_size: int = 100 * 1024 * 1024  # 100 MB (per ROADMAP)
    # Streaming buffer size when reading UploadFile.
    stream_chunk_size: int = 1024 * 1024  # 1 MB
    # Filename length cap (matches DB column).
    max_filename_length: int = 255

    # ==================== Upload policy ====================
    # Extensions and MIME types that are BLOCKED (executable / dangerous).
    # Everything else is allowed.  This is safer than a closed whitelist
    # because new legitimate file types (e.g. .psd, .fig, .mp4) work out
    # of the box without a config change.
    blocked_extensions: str = (
        "exe,bat,cmd,com,msi,scr,pif,vbs,vbe,wsf,wsh,ps1,psm1,psd1,"
        "csh,ksh,sh,bash,zsh,"
        "dll,sys,drv,inf,reg,rgs,"
        "application,app,bin,cpl,msp,hta,cpl,jse"
    )
    blocked_mime_types: str = (
        "application/x-executable,"
        "application/x-msdownload,"
        "application/x-ms-shortcut,"
        "application/x-windows-shortcut,"
        "application/x-bat,"
        "application/x-cmd,"
        "application/x-vbs,"
        "application/x-vbe,"
        "application/x-wsf,"
        "application/x-wsh,"
        "application/x-ps1,"
        "application/x-csh,"
        "application/x-ksh,"
        "application/x-sh,"
        "application/x-ms-installer"
    )

    # Preview-capable extensions (used by frontend to decide what to show).
    # Extensions NOT in this list are still uploadable, but the preview
    # modal shows "Preview unavailable".
    previewable_extensions: str = (
        "jpg,jpeg,png,gif,webp,svg,pdf,txt,csv,json,doc,docx,xls,xlsx,ppt,pptx"
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
            {
                "change-this-in-production",
                "your-super-secret-jwt-key-change-in-production",
            }
        )
    )

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # ==================== Validators ====================

    @field_validator(
        "blocked_extensions", "blocked_mime_types", "previewable_extensions"
    )
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def blocked_ext_set(self) -> FrozenSet[str]:
        return frozenset(
            e.strip().lower().lstrip(".")
            for e in self.blocked_extensions.split(",")
            if e.strip()
        )

    @property
    def blocked_mime_set(self) -> FrozenSet[str]:
        return frozenset(
            m.strip().lower() for m in self.blocked_mime_types.split(",") if m.strip()
        )

    @property
    def previewable_ext_set(self) -> FrozenSet[str]:
        return frozenset(
            e.strip().lower().lstrip(".")
            for e in self.previewable_extensions.split(",")
            if e.strip()
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

"""
Domain exceptions for File Service.

These exceptions are raised by the service / repository layer and are mapped
to HTTP responses in a single place (``src.api.exception_handlers``). The
service layer MUST NOT raise ``HTTPException`` — keeping it HTTP-agnostic
makes the services reusable from other transports (CLI jobs, message
consumers, ...) and gives us a single, auditable place to map errors.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class DomainError(Exception):
    """Base class for all file-service domain errors."""

    status_code: int = 500
    code: str = "internal_error"
    headers: Dict[str, str] = {}

    def __init__(
        self,
        detail: Optional[str] = None,
        *,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = detail or self.code
        super().__init__(message)
        self.detail = message
        self.extra = extra or {}


# ==================== Auth ====================


class AuthenticationError(DomainError):
    """Caller is not authenticated or the token is invalid."""

    status_code = 401
    code = "unauthenticated"
    headers = {"WWW-Authenticate": "Bearer"}


class AccessDenied(DomainError):
    """Authenticated user is not allowed to act on this resource."""

    status_code = 403
    code = "access_denied"


# ==================== Not Found ====================


class FileNotFound(DomainError):
    status_code = 404
    code = "file_not_found"


class FolderNotFound(DomainError):
    status_code = 404
    code = "folder_not_found"


# ==================== Validation ====================


class InvalidFileName(DomainError):
    status_code = 400
    code = "invalid_filename"


class UnsupportedFileType(DomainError):
    status_code = 415
    code = "unsupported_file_type"


class PayloadTooLarge(DomainError):
    status_code = 413
    code = "payload_too_large"


# ==================== Resource state ====================


class QuotaExceeded(DomainError):
    status_code = 413
    code = "quota_exceeded"


class CycleDetected(DomainError):
    """Tried to move a folder into one of its descendants."""

    status_code = 409
    code = "cycle_detected"


class ConflictError(DomainError):
    """Generic business conflict (e.g. duplicate name in the same folder)."""

    status_code = 409
    code = "conflict"


class RateLimitExceeded(DomainError):
    """Too many requests — contract-compliant 429 response."""

    status_code = 429
    code = "rate_limit_exceeded"

    def __init__(
        self,
        detail: Optional[str] = None,
        *,
        retry_after: int = 30,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged = dict(extra or {})
        merged.setdefault("retry_after", retry_after)
        super().__init__(detail or "Rate limit exceeded", extra=merged)
        self.headers = {"Retry-After": str(retry_after)}


class FileNameConflict(DomainError):
    """
    Raised when an upload would collide with an existing active file
    in the same folder (Phase 4.4).

    ``suggested_name`` is the first available disambiguator, e.g.
    ``"report (1).pdf"`` for a conflict on ``"report.pdf"``.  The
    client can either retry with the suggestion or pass
    ``?on_conflict=rename`` to have the server pick one automatically.
    """

    code = "file_name_conflict"
    status_code = 409

    def __init__(
        self,
        detail: Optional[str] = None,
        *,
        suggested_name: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged = dict(extra or {})
        if suggested_name is not None:
            merged.setdefault("suggested_name", suggested_name)
        super().__init__(detail, extra=merged)
        self.suggested_name = suggested_name

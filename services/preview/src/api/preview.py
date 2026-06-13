"""Preview endpoints — text extraction for non-browser-native formats."""

from __future__ import annotations

import structlog
import uuid as _uuid
from fastapi import APIRouter, Header, HTTPException, status

from src.schemas.preview import TextPreviewResponse
from src.services.file_client import fetch_file_bytes
from src.services.rate_limiter import check_rate_limit
from src.services.preview import extract_preview

logger = structlog.get_logger()

router = APIRouter(prefix="/api/preview", tags=["preview"])


# ── Helpers ──────────────────────────────────────────────────────


def _validate_file_id(file_id: str) -> str:
    """Validate that file_id is a valid UUID to prevent SSRF via path traversal."""
    try:
        _uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file ID format",
        )
    return file_id


def _require_auth_header(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    return authorization


# ── Endpoints ────────────────────────────────────────────────────


@router.get("/")
async def root():
    return {
        "message": "Preview Service is running",
        "version": "1.0.0",
        "generated_previews_enabled": True,
        "supported_text_previews": [
            "txt",
            "csv",
            "json",
            "docx",
            "xlsx",
        ],
        "note": "Images and PDFs can still use direct file download preview.",
    }


@router.get("/{file_id}", response_model=TextPreviewResponse)
async def get_preview(file_id: str, authorization: str | None = Header(default=None)):
    _validate_file_id(file_id)
    auth_header = _require_auth_header(authorization)

    # Rate limit by token prefix (first 16 chars) to avoid storing full JWT.
    rate_key = authorization[:16] if authorization else "anonymous"
    check_rate_limit(rate_key)

    logger.info("preview_request", file_id=file_id)

    content, mime_type = await fetch_file_bytes(file_id, auth_header)
    return extract_preview(content, mime_type)


@router.get("/{file_id}/thumbnail")
async def get_thumbnail(
    file_id: str,
    authorization: str | None = Header(default=None),
):
    _validate_file_id(file_id)
    _require_auth_header(authorization)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Thumbnails are not enabled yet",
    )


@router.post("/{file_id}/generate")
async def generate_preview(
    file_id: str,
    authorization: str | None = Header(default=None),
):
    _validate_file_id(file_id)
    _require_auth_header(authorization)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Background preview generation is not enabled yet",
    )


@router.delete("/{file_id}")
async def delete_preview(
    file_id: str,
    authorization: str | None = Header(default=None),
):
    _validate_file_id(file_id)
    _require_auth_header(authorization)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Stored previews are not enabled yet",
    )

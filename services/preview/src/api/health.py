"""Health-check endpoint."""

from __future__ import annotations

import structlog
from fastapi import APIRouter

from src.config import settings
from src.services.file_client import get_http_client

logger = structlog.get_logger()

router = APIRouter()


@router.get("/health")
async def health_check():
    file_service_ok = True
    try:
        client = get_http_client()
        resp = await client.get(f"{settings.file_service_url.rstrip('/')}/health")
        file_service_ok = resp.status_code == 200
    except Exception:
        file_service_ok = False

    healthy = file_service_ok
    return {
        "status": "healthy" if healthy else "degraded",
        "service": "preview",
        "file_service": "healthy" if file_service_ok else "unreachable",
    }

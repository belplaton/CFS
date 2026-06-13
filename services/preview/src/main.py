"""
Preview Service.

This service generates text-oriented previews for formats browsers do
not render well on their own, while browser-native previews (images /
PDFs) can still be fetched directly from the file service.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.middleware import RequestIDMiddleware
from src.api import preview_router, health_router

# ── Re-exports for backward-compatible test patches ──────────────
# Tests that patch ``src.main.<name>`` will continue to work because
# endpoint modules import directly from their source modules; however,
# keeping these names importable from main avoids surprise breakage in
# any downstream tooling that reaches into main for them.
from src.services.file_client import get_http_client as _get_http_client  # noqa: F401
from src.services.file_client import _http_client  # noqa: F401
from src.services.file_client import fetch_file_bytes as _fetch_file_bytes  # noqa: F401
from src.services.rate_limiter import _rate_limit_store  # noqa: F401
from src.services.rate_limiter import (
    RATE_LIMIT_MAX_REQUESTS as _RATE_LIMIT_MAX_REQUESTS,
)  # noqa: F401
from src.services.preview import TEXT_MIME_TYPES  # noqa: F401
from src.services.preview import DOCX_MIME_TYPE  # noqa: F401
from src.services.preview import XLSX_MIME_TYPE  # noqa: F401
from src.schemas.preview import TextPreviewResponse  # noqa: F401


# ── Application ──────────────────────────────────────────────────

app = FastAPI(
    title="Cloud Storage Preview Service",
    description="File preview generation service for Cloud File Storage",
    version="1.0.0",
    docs_url="/docs/preview",
    redoc_url="/redoc/preview",
    openapi_url="/openapi/preview.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

app.include_router(health_router)
app.include_router(preview_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

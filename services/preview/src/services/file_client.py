"""HTTP client for proxying requests to file-service."""

from __future__ import annotations

import httpx
import structlog
from fastapi import HTTPException, status

from src.config import settings

logger = structlog.get_logger()

# Reused across requests — httpx handles connection pooling internally.
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client


async def fetch_file_bytes(file_id: str, authorization: str) -> tuple[bytes, str]:
    """Download file content from file-service, enforcing preview size limit.

    Returns ``(content, mime_type)``.
    Raises ``HTTPException`` on transport / upstream errors.
    """
    url = f"{settings.file_service_url.rstrip('/')}/api/files/{file_id}/download"
    headers = {"Authorization": authorization}
    if settings.service_api_key:
        headers["X-API-Key"] = settings.service_api_key

    client = get_http_client()
    try:
        response = await client.get(url, headers=headers)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="File service request timed out",
        )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Preview service cannot reach file service",
        )

    if response.status_code >= 400:
        # Sanitize upstream errors: never forward internal details to clients.
        if response.status_code >= 500:
            detail = "File service error"
        else:
            detail = response.text or "Unable to fetch source file"
        raise HTTPException(status_code=response.status_code, detail=detail)

    # Stream-read with size limit to avoid OOM on large files.
    # Use bytearray for O(n) concatenation instead of bytes O(n²).
    content = bytearray()
    async for chunk in response.aiter_bytes(8192):
        content.extend(chunk)
        if len(content) > settings.preview_max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum preview size of {settings.preview_max_size} bytes",
            )

    mime_type = response.headers.get("content-type", "").split(";")[0].strip()
    return bytes(content), mime_type

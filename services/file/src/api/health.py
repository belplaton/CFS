"""
Health-check endpoint.

Phase 2.9: previously a static "ok" — now actively probes the
external dependencies.  Returns 200 when every dependency responds in
time, 503 when at least one is unhealthy.  Body is JSON so load
balancers and operators can see which subsystem is down.

The handler never raises: any probe failure is captured in the
response and logged so an outage leaves a paper trail.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.config import settings
from src.models import async_session
from src.utils.logging import get_logger
from src.utils.minio_client import get_minio_client
from src.utils.rate_limiter import get_redis


logger = get_logger("health")

router = APIRouter(tags=["Health"])


# ==================== Individual probes ====================


async def _probe_db() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000, 1)}


async def _probe_minio() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        client = get_minio_client()
        # ``bucket_exists`` issues a HEAD request to MinIO.
        # We run it in a thread to keep the event loop unblocked.
        exists = await asyncio.to_thread(client.bucket_exists, settings.minio_bucket)
        if not exists:
            return {"ok": False, "error": f"bucket '{settings.minio_bucket}' missing"}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000, 1)}


async def _probe_redis() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        await get_redis().ping()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {"ok": True, "latency_ms": round((time.perf_counter() - started) * 1000, 1)}


_PROBES: list[tuple[str, Callable[[], Awaitable[Dict[str, Any]]]]] = [
    ("database", _probe_db),
    ("minio", _probe_minio),
    ("redis", _probe_redis),
]


# ==================== Endpoint ====================


@router.get("/health")
async def health() -> JSONResponse:
    """
    Aggregate health check.

    * 200 + ``{"status": "healthy"}`` when every probe succeeds.
    * 503 + per-probe details when any probe fails.
    """
    results: Dict[str, Dict[str, Any]] = {}
    healthy = True

    for name, probe in _PROBES:
        result = await probe()
        results[name] = result
        if not result.get("ok"):
            healthy = False
            logger.warning(
                "health.probe_failed", subsystem=name, error=result.get("error")
            )

    body: Dict[str, Any] = {
        "status": "healthy" if healthy else "unhealthy",
        "service": "file",
        "checks": results,
    }
    return JSONResponse(
        status_code=200 if healthy else 503,
        content=body,
    )

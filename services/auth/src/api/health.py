"""
Health-check endpoint for Auth Service.

Phase 3: previously a static "ok" — now actively probes the database.
Returns 200 when the DB responds in time, 503 when it does not.  The
body is JSON so operators can see which subsystem is down.

The handler never raises: any probe failure is captured in the
response and logged so an outage leaves a paper trail.
"""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from src.models import async_session
from src.utils.logging import get_logger


logger = get_logger("health")
router = APIRouter(tags=["Health"])


async def _probe_db() -> dict[str, Any]:
    started = time.perf_counter()
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "latency_ms": round((time.perf_counter() - started) * 1000, 1),
    }


@router.get("/health")
async def health() -> JSONResponse:
    """Aggregate health check.

    * 200 + ``{"status": "healthy"}`` when every probe succeeds.
    * 503 + per-probe details when any probe fails.
    """
    db_result = await _probe_db()
    healthy = bool(db_result.get("ok"))

    body: dict[str, Any] = {
        "status": "healthy" if healthy else "unhealthy",
        "service": "auth",
        "checks": {"database": db_result},
    }
    if not healthy:
        logger.warning(
            "health.probe_failed", subsystem="database", error=db_result.get("error")
        )
    return JSONResponse(
        status_code=200 if healthy else 503,
        content=body,
    )

"""
Per-request access log middleware.

Emits a single ``http.request`` structlog event for every HTTP
response, carrying the essentials an operator needs to triage:

* method, path, status_code
* duration_ms
* request_id (from :class:`RequestIDMiddleware`)
* client_ip, user_agent (from :class:`RequestMetaMiddleware`)

The event lives *outside* the exception path: when a request raises
the framework still calls us, so a 5xx leaves a trail.  We never
re-raise from here — the middleware is observational only.

Health probes and OpenAPI documentation are excluded by default
to keep the log signal-to-noise ratio high.
"""
from __future__ import annotations

import time
from typing import Awaitable, Callable, Iterable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logging import get_logger


SERVICE_NAME = "file-service"


logger = get_logger("http.access")


# Paths that fire a request every few seconds.  Logging them at INFO
# drowns the rest of the audit signal — promote them to DEBUG so an
# operator can opt in via LOG_LEVEL=DEBUG.
_DEFAULT_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi",
)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Log one structured event per HTTP request.

    Order in the middleware stack (registered last = outermost):

        RequestIDMiddleware        (sets request_id_var)
        RequestMetaMiddleware      (sets client_ip_var, user_agent_var)
        AccessLogMiddleware        (reads all three, emits event)
        ...application...
    """

    def __init__(
        self,
        app,
        *,
        excluded_prefixes: Optional[Iterable[str]] = None,
        slow_request_threshold_ms: int = 1000,
    ) -> None:
        super().__init__(app)
        self._excluded = tuple(excluded_prefixes or _DEFAULT_EXCLUDED_PREFIXES)
        self._slow_ms = slow_request_threshold_ms

    def _is_excluded(self, path: str) -> bool:
        return any(path.startswith(p) for p in self._excluded)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        method = request.method

        # Cheap pre-check: skip the work entirely for noisy paths.
        if self._is_excluded(path):
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500  # assume failure until proven otherwise
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            event = (
                "http.request_slow"
                if duration_ms >= self._slow_ms
                else "http.request"
            )
            # Read the values from ``request.state`` rather than the
            # contextvars: by the time this finally runs the inner
            # ``RequestIDMiddleware``/``RequestMetaMiddleware`` have
            # already reset their tokens.  ``request.state`` survives
            # the inner finally blocks.
            request_id = getattr(request.state, "request_id", None)
            meta = getattr(request.state, "request_meta", None)
            level = logger.warning if status_code >= 500 else logger.info
            level(
                event,
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                client_ip=meta.ip if meta else None,
                user_agent=meta.user_agent if meta else None,
                service=SERVICE_NAME,
            )

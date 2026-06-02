"""
Per-request access log middleware (auth service).

Mirrors :mod:`file.src.middleware.access_log` so the two services
emit log lines with the same shape, fields and event names.

Why duplicate instead of share?
    The two services already have slightly different config schemas
    (the auth service has no MinIO client, different env names) and
    the cost of cross-service Python imports outweighs the benefit
    of de-duplicating ~80 lines.
"""
from __future__ import annotations

import time
from typing import Awaitable, Callable, Iterable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logging import get_logger


logger = get_logger("http.access")


# Health and OpenAPI docs are noisy and would otherwise dominate
# every second of log output during a load test.
_DEFAULT_EXCLUDED_PREFIXES: tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Log one ``http.request`` event per response.

    Order (outermost first):

        RequestIDMiddleware -> AccessLogMiddleware -> ...handler
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

        if self._is_excluded(path):
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
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
            # Read from request.state: by the time this finally runs
            # the inner ``RequestIDMiddleware`` has already reset its
            # contextvar.  State survives the inner finally blocks.
            request_id = getattr(request.state, "request_id", None)
            level = logger.warning if status_code >= 500 else logger.info
            level(
                event,
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                service="auth-service",
            )

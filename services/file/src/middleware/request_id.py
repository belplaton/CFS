"""
ASGI middleware: generate (or accept) ``X-Request-ID`` per request and
expose it to structlog's context.
"""
from __future__ import annotations

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logging import bind_contextvars, clear_contextvars, get_logger, request_id_var


_HEADER = "X-Request-ID"
_logger = get_logger("http")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    - Reads ``X-Request-ID`` from the incoming request (or generates one).
    - Stores it in :data:`request_id_var` and structlog's context.
    - Echoes the value back in the response header.
    - Always clears the context after the request, even on errors.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get(_HEADER) or uuid4().hex
        token = request_id_var.set(request_id)
        clear_contextvars()
        bind_contextvars(request_id=request_id)

        try:
            response: Response = await call_next(request)
        except Exception:
            _logger.exception("request.failed", method=request.method, path=request.url.path)
            raise
        finally:
            request_id_var.reset(token)
            clear_contextvars()

        response.headers[_HEADER] = request_id
        return response

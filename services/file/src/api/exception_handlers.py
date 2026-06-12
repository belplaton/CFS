"""
Centralised exception → HTTP response mapping.

Keeping this in one module means services stay HTTP-agnostic: they raise
domain exceptions, and the API layer turns them into well-formed responses.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.exceptions import DomainError
from src.utils.logging import get_logger


logger = get_logger(__name__)


def _error_payload(
    code: str, detail: str, extra: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    body: Dict[str, Any] = {"error": code, "detail": detail}
    if extra:
        body["extra"] = extra
    return body


async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(exc.code, exc.detail, exc.extra),
        headers=exc.headers or None,
    )


async def http_exception_handler(
    _: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # FastAPI's built-in ``HTTPException`` — used by deps that still raise it
    # (e.g. bearer-scheme auto-errors). Map to the same shape.
    code_map = {
        400: "bad_request",
        401: "unauthenticated",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        413: "payload_too_large",
        415: "unsupported_media_type",
        422: "validation_error",
    }
    code = code_map.get(exc.status_code, "error")
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_payload(code, detail),
        headers=exc.headers or None,
    )


async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_error_payload(
            "validation_error",
            "Request validation failed",
            {"errors": exc.errors()},
        ),
    )


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    # Never leak internal details to the caller, but log them server-side
    # with traceback so on-call has something to work with.
    logger.exception("unhandled.exception", error_type=type(exc).__name__)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_error_payload("internal_error", "Internal server error"),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

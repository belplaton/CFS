"""
Domain exception handlers for the Auth service.

Translates ``DomainError`` subclasses into structured JSON responses
with a stable error ``code`` (suitable for client-side branching)
and a ``Retry-After`` header on rate-limit responses.
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    DomainError,
    InvalidTokenError,
    RateLimitError,
    UserAlreadyExistsError,
    UserNotFoundError,
    ValidationError,
)
from src.utils.logging import get_logger


logger = get_logger(__name__)


def _payload(code: str, message: str, **details) -> dict:
    body: dict = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return body


def install_exception_handlers(app: FastAPI) -> None:
    """Register handlers for every domain error type."""

    @app.exception_handler(DomainError)
    async def _domain(request: Request, exc: DomainError):
        if not isinstance(exc, RateLimitError):
            logger.warning(
                "domain_error",
                code=exc.code,
                message=exc.message,
                path=request.url.path,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(exc.code, exc.message, **exc.details),
            headers={"WWW-Authenticate": "Bearer"} if isinstance(exc, (AuthenticationError, InvalidTokenError)) else None,
        )

    @app.exception_handler(RateLimitError)
    async def _rate_limit(request: Request, exc: RateLimitError):
        logger.warning(
            "rate_limited",
            path=request.url.path,
            retry_after=exc.retry_after,
            limit=exc.limit,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(
                exc.code,
                exc.message,
                retry_after=exc.retry_after,
                limit=exc.limit,
                window=exc.window,
            ),
            headers={"Retry-After": str(exc.retry_after)},
        )

    # Concrete handlers are registered for documentation (and to give
    # OpenAPI consumers a stable target).  The DomainError catch-all
    # above handles the actual response.
    for exc_type in (
        AuthenticationError,
        AuthorizationError,
        UserNotFoundError,
        UserAlreadyExistsError,
        InvalidTokenError,
        ValidationError,
        DatabaseError,
    ):
        app.exception_handler(exc_type)(_domain)

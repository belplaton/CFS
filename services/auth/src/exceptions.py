"""
Domain exceptions for the Auth service.

Each exception carries a stable ``code`` that the global handler
maps to an HTTP status.  Services must raise these, never
``HTTPException`` — the API layer only translates.
"""
from __future__ import annotations


class DomainError(Exception):
    """Base class for all Auth domain errors."""

    code: str = "domain_error"
    status_code: int = 400

    def __init__(self, message: str = "", **details):
        super().__init__(message)
        self.message = message
        self.details = details


class AuthenticationError(DomainError):
    code = "authentication_error"
    status_code = 401


class AuthorizationError(DomainError):
    code = "authorization_error"
    status_code = 403


class UserNotFoundError(DomainError):
    code = "user_not_found"
    status_code = 404


class UserAlreadyExistsError(DomainError):
    code = "user_already_exists"
    status_code = 409


class InvalidTokenError(DomainError):
    code = "invalid_token"
    status_code = 401


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class RateLimitError(DomainError):
    code = "rate_limit_exceeded"
    status_code = 429

    def __init__(self, retry_after: int, limit: int, window: int, message: str = ""):
        super().__init__(message or f"Rate limit exceeded: {limit} requests per {window}s")
        self.retry_after = retry_after
        self.limit = limit
        self.window = window


class ConfigurationError(DomainError):
    code = "configuration_error"
    status_code = 500


class DatabaseError(DomainError):
    code = "database_error"
    status_code = 500

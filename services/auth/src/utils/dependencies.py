"""
Dependencies for Auth Service.

Phase 3 changes:

* The ``sub`` claim is now a UUID string (the cross-service contract).
  Tokens with an integer sub are rejected — no silent coercion, no
  hidden compatibility mode.
* ``decode_token`` validates ``iss``/``aud``/``type``; the
  ``credentials_exception`` is raised uniformly for any failure.
* The dependency returns the ORM ``User`` object so handlers can use
  ``current_user.id`` (UUID) directly.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import AuthenticationError, AuthorizationError
from src.models import get_db
from src.models.user import User
from src.repositories.user import UserRepository
from src.utils.security import decode_token


# Security scheme — auto_error=False so we raise our own domain error
# (mapped to a 401 with consistent body) instead of FastAPI's default 403.
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the access token and return the matching ``User`` row.

    Raises ``AuthenticationError`` (401 + WWW-Authenticate: Bearer) for
    any failure (missing token, wrong type, bad issuer/audience, unknown
    user, …) and ``AuthorizationError`` (403) for inactive accounts.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Could not validate credentials")

    try:
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise AuthenticationError("Could not validate credentials") from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Could not validate credentials")

    sub = payload.get("sub")
    if sub is None:
        raise AuthenticationError("Could not validate credentials")

    try:
        user_id = UUID(str(sub))
    except (ValueError, TypeError) as exc:
        raise AuthenticationError("Could not validate credentials") from exc

    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise AuthenticationError("Could not validate credentials")

    if not user.is_active:
        raise AuthorizationError("Inactive user")

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Same as :func:`get_current_user` but additionally requires ``is_verified``."""
    if not current_user.is_verified:
        raise AuthorizationError("Email not verified")
    return current_user

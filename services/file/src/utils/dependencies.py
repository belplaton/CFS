"""
Authentication dependencies for File Service.

Validates the Bearer JWT issued by the Auth Service and returns the
caller's user id (UUID).  Enforces:

* ``type=access`` — refresh tokens cannot be used to call data APIs.
* ``iss=auth-service`` and ``aud=cloud-storage`` — tokens from a
  different issuer or for a different audience are rejected.
* ``sub`` is a UUID string — non-UUID subjects are rejected (this
  was previously coerced from int; the Auth service now issues
  UUIDs directly so the legacy fallback is gone).

Cross-service contract note
---------------------------
The cross-service id namespace is the UUID issued by Auth.  Any new
service joining the platform should accept UUID subs and refuse ints.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import settings
from src.exceptions import AuthenticationError
from src.utils.logging import get_logger


logger = get_logger(__name__)


# ``auto_error=False`` lets us raise our own domain exception (mapped to a
# 401 with consistent body) instead of FastAPI's default 403.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> UUID:
    """Decode the access token and return the caller's user id (UUID)."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Missing bearer token")

    decode_kwargs: dict = {
        "algorithms": [settings.jwt_algorithm],
        "audience": settings.jwt_audience,
        "issuer": settings.jwt_issuer,
        "options": {"require": ["exp", "sub", "type"]},
    }

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            **decode_kwargs,
        )
    except JWTError as exc:
        raise AuthenticationError("Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise AuthenticationError("Token is not an access token")

    sub = payload.get("sub")
    if sub is None:
        raise AuthenticationError("Token is missing subject claim")
    if not isinstance(sub, str):
        raise AuthenticationError("Token subject must be a string")

    try:
        return UUID(sub)
    except (ValueError, TypeError) as exc:
        # No more silent integer coercion — Auth must issue UUIDs.
        raise AuthenticationError(
            "Token subject is not a valid user id (expected UUID)"
        ) from exc

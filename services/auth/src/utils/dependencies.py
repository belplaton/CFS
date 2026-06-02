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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import get_db
from src.models.user import User
from src.schemas import TokenData
from src.utils.security import decode_token


# Security scheme — auto_error=False so we raise our own domain error
# (mapped to a 401 with consistent body) instead of FastAPI's default 403.
security = HTTPBearer(auto_error=False)


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode the access token and return the matching ``User`` row.

    Raises ``HTTPException(401)`` for any failure (missing token,
    wrong type, bad issuer/audience, unknown user, ...).
    """
    if credentials is None or not credentials.credentials:
        raise _credentials_error()

    try:
        # ``decode_token`` enforces iss / aud / exp / type.  The
        # ``expected_type="access"`` is enforced by the caller via
        # ``is_access_token`` so the error message can stay neutral.
        payload = decode_token(credentials.credentials)
    except JWTError as exc:
        raise _credentials_error() from exc

    if payload.get("type") != "access":
        raise _credentials_error()

    sub = payload.get("sub")
    if sub is None:
        raise _credentials_error()

    # Auth service issues UUID strings in ``sub``; anything else is a
    # malformed token (or a token from a non-migrated peer service).
    try:
        user_id = UUID(str(sub))
    except (ValueError, TypeError) as exc:
        raise _credentials_error() from exc

    token_data = TokenData(user_id=user_id, email=payload.get("email"))

    # Lazy import to avoid a circular dependency at module load time.
    from src.services.user_service import UserService

    user_service = UserService(db)
    user = await user_service.get_user_by_id(token_data.user_id)
    if user is None:
        raise _credentials_error()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Same as :func:`get_current_user` but additionally requires ``is_verified``."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified",
        )
    return current_user

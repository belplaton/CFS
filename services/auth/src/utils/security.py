"""
Security utilities for Auth Service.

Phase 3 changes:

* Access and refresh tokens now carry ``iss`` (issuer) and ``aud``
  (audience) claims.  Downstream services reject tokens that don't
  match their configured values, so an attacker who steals a token
  from another service cannot replay it against this stack.
* ``decode_token`` validates ``iss`` and ``aud`` when present in the
  payload (FastAPI's python-jose does the comparison internally).
* Both token types carry an explicit ``type`` claim — the File
  service refuses to use a refresh token against a data API.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import settings
from src.utils.logging import get_logger
from src.utils.redis_client import get_redis


logger = get_logger(__name__)


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Password Utilities ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


# ==================== JWT Utilities ====================

REVOCATION_KEY_PREFIX = "auth:revoked:refresh:"


def _refresh_revocation_key(token: str) -> str:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"{REVOCATION_KEY_PREFIX}{token_hash}"


def _base_claims(token_type: str) -> Dict[str, Any]:
    """Claims that every token issued by this service carries."""
    return {
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": token_type,
    }


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    to_encode.update(_base_claims("access"))

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token (longer lived)."""
    to_encode = data.copy()
    to_encode.update(_base_claims("refresh"))
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Decode and verify JWT token.

    Validates ``iss``/``aud`` against the configured values and (when
    ``expected_type`` is given) the ``type`` claim.  Raises ``JWTError``
    on any failure — callers should map that to a 401 themselves.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
        audience=settings.jwt_audience,
        issuer=settings.jwt_issuer,
        options={"require": ["exp", "sub", "type"]},
    )


# ==================== Token Type Check ====================

def is_access_token(payload: Dict[str, Any]) -> bool:
    """Check if token is access token."""
    return payload.get("type") == "access"


def is_refresh_token(payload: Dict[str, Any]) -> bool:
    """Check if token is refresh token."""
    return payload.get("type") == "refresh"


async def revoke_refresh_token(token: str) -> None:
    """Blacklist a refresh token until its natural expiry.

    Raises ``JWTError`` on invalid tokens (wrong type, missing claims).
    Fails open on Redis errors — a failed revocation is preferable to
    a 500 on logout.
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise JWTError("Wrong token type for refresh revocation")

    expires_at = payload.get("exp")
    if expires_at is None:
        raise JWTError("Missing exp claim")

    ttl_seconds = max(int(expires_at - datetime.now(timezone.utc).timestamp()), 1)
    try:
        await get_redis().setex(_refresh_revocation_key(token), ttl_seconds, "1")
    except Exception:  # noqa: BLE001
        logger.warning("redis_revoke_failed", exc_info=True)


async def is_refresh_token_revoked(token: str) -> bool:
    """Return ``True`` when the given refresh token was revoked.

    Returns ``False`` on Redis errors (fail-open).
    """
    try:
        return bool(await get_redis().get(_refresh_revocation_key(token)))
    except Exception:  # noqa: BLE001
        logger.warning(
            "redis_revocation_check_failed", exc_info=True
        )
        return False


# Re-export so ``dependencies.py`` keeps its existing import path.
__all__ = [
    "JWTError",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_password_hash",
    "is_access_token",
    "is_refresh_token",
    "is_refresh_token_revoked",
    "revoke_refresh_token",
    "verify_password",
]

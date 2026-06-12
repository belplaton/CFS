"""
Helpers used by both the test modules and ``conftest.py``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Union
from uuid import UUID

from jose import jwt as jose_jwt


USER_ALICE = UUID("11111111-1111-1111-1111-111111111111")
USER_BOB = UUID("22222222-2222-2222-2222-222222222222")


def make_jwt(
    user_id: Union[str, UUID],
    *,
    token_type: str = "access",
    secret: str | None = None,
    expires_in: timedelta = timedelta(minutes=15),
) -> str:
    """Build a signed JWT for use in auth-bypass tests."""
    secret = secret or "test-secret"
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_in,
    }
    return jose_jwt.encode(payload, secret, algorithm="HS256")

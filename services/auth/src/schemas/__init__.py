"""
Pydantic schemas for Auth Service (Phase 3: ConfigDict, UUID ids).

The ``UserResponse.id`` field is now a ``UUID`` to match the database
column type.  All other shapes are unchanged so the public REST
contract is only "breaking" in the sense that clients that used
``id`` as an int must switch to a string-typed parser.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==================== Auth Schemas ====================


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token payload (used internally)."""

    user_id: Optional[UUID] = None
    email: Optional[str] = None


# ==================== User Schemas ====================


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User registration schema."""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_verified: bool
    is_admin: bool
    storage_quota: int
    used_storage: int
    created_at: datetime
    last_login: Optional[datetime] = None


# ==================== Verification Schemas ====================


class EmailVerificationRequest(BaseModel):
    """Email verification request."""

    token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== Google OAuth Schemas ====================


class GoogleAuthRequest(BaseModel):
    """Google OAuth request."""

    code: str
    redirect_uri: str

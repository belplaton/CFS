"""
Pydantic schemas for Auth Service
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


# ==================== Auth Schemas ====================

class Token(BaseModel):
    """Token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload schema"""
    user_id: Optional[int] = None
    email: Optional[str] = None


# ==================== User Schemas ====================

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User registration schema"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    is_active: bool
    is_verified: bool
    is_admin: bool
    storage_quota: int
    used_storage: int
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== Verification Schemas ====================

class EmailVerificationRequest(BaseModel):
    """Email verification request"""
    token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


# ==================== Google OAuth Schemas ====================

class GoogleAuthRequest(BaseModel):
    """Google OAuth request"""
    code: str
    redirect_uri: str

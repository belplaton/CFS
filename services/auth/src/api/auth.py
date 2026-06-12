"""
Auth API endpoints
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import AuthenticationError
from src.models import get_db
from src.models.user import User
from src.schemas import (
    UserCreate, UserLogin, Token, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest, ActionLinkResponse, LogoutRequest,
)
from src.services.user_service import UserService
from src.utils.dependencies import get_current_user, security
from src.utils.security import decode_token, is_refresh_token_revoked, revoke_refresh_token
from src.utils.rate_limiter import (
    rate_limit_login,
    rate_limit_register,
    rate_limit_password_reset,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_register)],
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user

    - **email**: User's email address
    - **password**: User's password (min 8 characters)
    - **full_name**: Optional full name
    """
    user_service = UserService(db)

    # Create user
    user = await user_service.create_user(user_data)

    # Create tokens
    tokens = await user_service.create_tokens_for_user(user)

    return tokens


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(rate_limit_login)],
)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login with email and password

    - **email**: Registered email
    - **password**: User's password
    """
    user_service = UserService(db)

    # Authenticate user
    user = await user_service.authenticate_user(credentials.email, credentials.password)

    if not user:
        # Add a small constant delay to make timing attacks harder.  The
        # rate limiter above is the primary defence; the delay is a
        # secondary mitigation against per-account credential stuffing.
        import asyncio
        await asyncio.sleep(1)
        raise AuthenticationError("Incorrect email or password")

    # Explicitly check bool value for SQLAlchemy columns
    if not bool(user.is_active):  # type: ignore[arg-type]
        raise AuthenticationError("Inactive user")

    # Create tokens
    tokens = await user_service.create_tokens_for_user(user)

    return tokens


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user info

    Requires Bearer token in Authorization header
    """
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token

    Uses a Bearer refresh token and returns a fresh access/refresh pair.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Could not validate credentials")

    try:
        payload = decode_token(credentials.credentials)
    except Exception as exc:  # noqa: BLE001
        raise AuthenticationError("Could not validate credentials") from exc

    if payload.get("type") != "refresh":
        raise AuthenticationError("Could not validate credentials")

    if await is_refresh_token_revoked(credentials.credentials):
        raise AuthenticationError("Could not validate credentials")

    sub = payload.get("sub")
    if sub is None:
        raise AuthenticationError("Could not validate credentials")

    try:
        user_id = UUID(str(sub))
    except (ValueError, TypeError) as exc:
        raise AuthenticationError("Could not validate credentials") from exc

    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if user is None:
        raise AuthenticationError("Could not validate credentials")
    if not bool(user.is_active):  # type: ignore[arg-type]
        raise AuthenticationError("Inactive user")
    return await user_service.create_tokens_for_user(user)


@router.post("/logout")
async def logout(
    request: LogoutRequest,
):
    """
    Revoke the provided refresh token.
    """
    try:
        await revoke_refresh_token(request.refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise AuthenticationError("Could not validate credentials") from exc

    return {"message": "Logged out successfully"}


@router.post(
    "/forgot-password",
    dependencies=[Depends(rate_limit_password_reset)],
    response_model=ActionLinkResponse,
)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Request password reset.
    """
    user_service = UserService(db)
    token, action_url = await user_service.request_password_reset(request.email)

    # Always return success to prevent email enumeration
    response = ActionLinkResponse(
        message="If email exists, password reset instructions will be sent",
    )
    if token and action_url and request.email:
        response.token = token
        response.action_url = action_url
    return response


@router.post(
    "/reset-password",
    dependencies=[Depends(rate_limit_password_reset)],
)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Reset password using token.
    """
    user_service = UserService(db)
    await user_service.reset_password_with_token(request.token, request.new_password)
    return {"message": "Password updated successfully"}


@router.post("/verify-email/request", response_model=ActionLinkResponse)
async def request_verify_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a fresh email verification token for the current user.
    """
    user_service = UserService(db)
    token, action_url = await user_service.request_email_verification(current_user)
    return ActionLinkResponse(
        message="Verification instructions generated",
        token=token,
        action_url=action_url,
    )


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify email using token.
    """
    user_service = UserService(db)
    user = await user_service.consume_email_verification_token(token)
    return {
        "message": "Email verified successfully",
        "email": user.email,
        "verified": True,
    }

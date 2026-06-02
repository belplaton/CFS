"""
Auth API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import get_db
from src.schemas import (
    UserCreate, UserLogin, Token, UserResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from src.services.user_service import UserService
from src.utils.dependencies import get_current_user
from src.utils.rate_limiter import (
    rate_limit_login,
    rate_limit_register,
    rate_limit_password_reset,
)
from src.models.user import User

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Explicitly check bool value for SQLAlchemy columns
    if not bool(user.is_active):  # type: ignore[arg-type]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

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
async def refresh_token():
    """
    Refresh access token using refresh token

    TODO: Implement refresh token logic
    """
    return {"message": "Refresh token endpoint - to be implemented"}


@router.post(
    "/forgot-password",
    dependencies=[Depends(rate_limit_password_reset)],
)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Request password reset

    TODO: Implement email sending
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(request.email)

    if user:
        # TODO: Generate token and send email
        pass

    # Always return success to prevent email enumeration
    return {"message": "If email exists, password reset instructions will be sent"}


@router.post(
    "/reset-password",
    dependencies=[Depends(rate_limit_password_reset)],
)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Reset password using token

    TODO: Implement token verification and password update
    """
    return {"message": "Password reset endpoint - to be implemented"}


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Verify email using token

    TODO: Implement email verification
    """
    return {"message": "Email verification endpoint - to be implemented"}

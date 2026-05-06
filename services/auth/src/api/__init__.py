"""
API routes package
"""
from fastapi import APIRouter

from src.api.auth import router as auth_router

# Main API router
api_router = APIRouter()
api_router.include_router(auth_router)

__all__ = ["api_router"]

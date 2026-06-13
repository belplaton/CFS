"""
API routes package
"""

from fastapi import APIRouter

from src.api.files import router as files_router
from src.api.folders import router as folders_router
from src.api.health import router as health_router
from src.api.internal import router as internal_router
from src.api.search import router as search_router
from src.api.trash import router as trash_router

api_router = APIRouter()
api_router.include_router(files_router)
api_router.include_router(folders_router)
api_router.include_router(trash_router)
api_router.include_router(search_router)
api_router.include_router(health_router)
api_router.include_router(internal_router)

__all__ = ["api_router"]

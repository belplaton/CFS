"""
Search API endpoint (Phase 1: thin wrapper over ``SearchService``).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import get_db
from src.schemas import SearchResponse
from src.services.search_service import SearchService
from src.utils.dependencies import get_current_user_id


router = APIRouter(prefix="/api/search", tags=["Search"])


@router.get("/", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=255),
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    results = await SearchService(db).search(user_id, q)
    return SearchResponse(results=results, total=len(results), query=q)

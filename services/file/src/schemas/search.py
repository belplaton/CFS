"""
Pydantic schemas for the search resource.
"""

from __future__ import annotations

from src.schemas.common import ItemResponse
from pydantic import BaseModel


class SearchResponse(BaseModel):
    """Body of GET /api/search/?q=... — matches a unified list of items."""

    results: list[ItemResponse]
    total: int
    query: str

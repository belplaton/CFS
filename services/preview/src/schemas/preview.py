"""Response models for preview endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class TextPreviewResponse(BaseModel):
    kind: str = "text"
    content: str
    truncated: bool = False

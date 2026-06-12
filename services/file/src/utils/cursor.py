"""
Cursor-based pagination helpers (Phase 4.5).

Why cursor instead of offset?
    * Stable under concurrent inserts — offset shifts if a row is
      inserted between page requests.
    * Index-friendly — ``WHERE (name, id) > (?, ?) ORDER BY name, id
      LIMIT n`` uses the same B-tree as the unfiltered ``ORDER BY``.
    * Stateless — the cursor carries everything the server needs;
      no per-user state on the server.

Cursor format
    Base64-url(JSON ``{"name": str, "id": UUID-строка}``).  The
    JSON envelope makes it trivial to add fields (e.g. ``ts`` for
    time-ordered feeds) without breaking older clients.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, NamedTuple, Optional
from uuid import UUID


class CursorError(ValueError):
    """Raised on a malformed / unverifiable cursor."""


class Cursor(NamedTuple):
    name: str
    id: UUID

    def encode(self) -> str:
        payload = json.dumps(
            {"name": self.name, "id": str(self.id)},
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")

    @classmethod
    def decode(cls, raw: str) -> "Cursor":
        if not raw:
            raise CursorError("empty cursor")
        # Restore base64 padding (we strip ``=`` on encode).
        padded = raw + "=" * (-len(raw) % 4)
        try:
            data: Dict[str, Any] = json.loads(
                base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            )
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise CursorError(f"cursor is not valid base64-json: {exc}") from exc
        try:
            return cls(name=str(data["name"]), id=UUID(str(data["id"])))
        except (KeyError, ValueError, TypeError) as exc:
            raise CursorError(f"cursor is missing required fields: {exc}") from exc

    @classmethod
    def try_decode(cls, raw: Optional[str]) -> Optional["Cursor"]:
        if raw is None or raw == "":
            return None
        return cls.decode(raw)

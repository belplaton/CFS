"""
Filename conflict resolution (Phase 4.4).

When a user uploads ``report.pdf`` to a folder that already contains
``report.pdf``, the service has three options:

* reject with a 409 + suggested name in the body — the user retries
  with the suggestion (or a different name);
* auto-rename — pick the first available ``report (1).pdf``,
  ``report (2).pdf`` ... and proceed silently;
* overwrite — replace the existing file.  **Not implemented**: this is
  destructive and we have no UX surface (no `If-Match` etc.) to make
  it safe.

The picker below produces the next available disambiguator.  It is
deliberately bounded — we only try up to ``max_attempts`` variants
before raising :class:`~src.exceptions.FileNameConflict`.  Anything
beyond that almost certainly indicates a bug in the upload path, not
a real user scenario.
"""
from __future__ import annotations

import os
import re
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import FileNameConflict
from src.repositories.file import FileRepository


# ``report.pdf`` → ``report (N).pdf`` — keep the extension, inject the
# disambiguator before the *last* dot.  Files without an extension just
# get the suffix appended.
_DOT = "."


def _split_name(filename: str) -> tuple[str, str]:
    """Return (stem, ext) where ext includes the leading dot or is empty."""
    _, ext = os.path.splitext(filename)
    stem = filename[: -len(ext)] if ext else filename
    return stem, ext


_DISAMBIG_RE = re.compile(r"^(?P<stem>.*?) \((?P<n>\d+)\)$")


def _next_variant(stem: str, ext: str, n: int) -> str:
    return f"{stem} ({n}){ext}"


async def find_available_name(
    db: AsyncSession,
    user_id: UUID,
    folder_id: Optional[UUID],
    desired: str,
    *,
    max_attempts: int = 1000,
) -> str:
    """
    Return ``desired`` if it is free, else the lowest ``desired (N)``
    (preserving the extension) that is free.

    Raises :class:`FileNameConflict` if no variant is found within
    ``max_attempts`` — protecting against pathological folders with
    thousands of ``report (1).pdf`` ... ``report (1000).pdf``.
    """
    existing = await FileRepository.list_existing_names_in_folder(
        db, user_id, folder_id
    )
    if desired not in existing:
        return desired

    stem, ext = _split_name(desired)
    # If the stem itself already ends in "(N)", strip that — otherwise
    # ``report (1).pdf`` colliding with ``report (1).pdf`` would yield
    # ``report (1) (1).pdf`` which is ugly.  We treat the existing
    # disambiguator as the *base* and continue from there.
    m = _DISAMBIG_RE.match(stem)
    base = m.group("stem") if m else stem
    start = int(m.group("n")) + 1 if m else 1

    for n in range(start, start + max_attempts):
        candidate = _next_variant(base, ext, n)
        if candidate not in existing:
            return candidate

    raise FileNameConflict(
        f"Could not find a free name for {desired!r} in this folder",
        suggested_name="(none available)",
        extra={"attempts": max_attempts},
    )


def suggest_rename(desired: str) -> str:
    """
    Cheap, allocation-free variant of :func:`find_available_name` that
    does *not* touch the database.  Used by the API layer to populate
    the 409 body so the client has something to retry with *before*
    they pay for the upload round-trip.

    The actual upload still re-checks against the DB; this is just a
    hint.  If the suggestion collides too, the real upload returns a
    409 with a fresh suggestion.
    """
    stem, ext = _split_name(desired)
    m = _DISAMBIG_RE.match(stem)
    if m:
        base = m.group("stem")
        n = int(m.group("n")) + 1
    else:
        base = stem
        n = 1
    return _next_variant(base, ext, n)

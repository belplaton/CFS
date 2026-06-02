"""
File-name and content-type validators for File Service.

Design notes
------------
- We intentionally allow non-ASCII characters in filenames (Cyrillic, emoji, ...).
  Only characters that are unsafe on any mainstream filesystem or transport
  (NUL, control chars, path separators, leading dots-only names) are stripped.
- Windows reserved names are blocked to avoid surprises if the file is ever
  re-downloaded onto a Windows client.
- We do NOT use ``werkzeug.secure_filename`` because it strips non-ASCII
  entirely, which is too aggressive for a user-facing file storage product.
- Content-type validation uses the value sent by the client. Magic-byte
  detection (libmagic) is intentionally out of scope for Phase 1; it will be
  added in a later phase so that we can detect mismatches between declared
  and actual content type.
"""
from __future__ import annotations

import os
import re
import unicodedata
import urllib.parse
from typing import Optional

from src.config import settings
from src.exceptions import InvalidFileName, UnsupportedFileType


# NUL and C0/C1 control characters except for tab (\x09), LF (\x0a), CR (\x0d).
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Path separators on either Windows or POSIX.
_PATH_SEPARATORS = {"/", "\\"}

# Reserved device names on Windows (case-insensitive, with or without extension).
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Filler name used when the sanitized result is empty.
_FALLBACK_NAME = "unnamed"


def _strip_path_components(raw: str) -> str:
    """Drop any directory components the browser may have included.

    The browser may send ``C:\\Users\\foo\\bar.txt`` or ``../../etc/passwd``
    as the filename. We collapse both POSIX and Windows separators first
    and then take only the trailing path component.
    """
    normalised = raw.replace("\\", "/")
    return os.path.basename(normalised)


def _is_pure_dots(name: str) -> bool:
    return bool(name) and all(ch == "." for ch in name)


def _is_windows_reserved(stem: str) -> bool:
    return stem.upper() in _WINDOWS_RESERVED


def sanitize_filename(raw: Optional[str]) -> str:
    """
    Return a safe, displayable filename derived from a user-supplied string.

    Raises ``InvalidFileName`` when the input cannot be turned into a usable
    name. The function is intentionally permissive about Unicode: the goal
    is to neutralize path-traversal and control-character attacks, not to
    enforce ASCII.
    """
    if raw is None:
        raise InvalidFileName("Filename is required")
    if not isinstance(raw, str):
        raise InvalidFileName("Filename must be a string")

    # NFKC normalises e.g. full-width slashes and other look-alike glyphs.
    name = unicodedata.normalize("NFKC", raw).strip()

    name = _strip_path_components(name)
    if not name or _is_pure_dots(name):
        name = _FALLBACK_NAME

    # Remove control characters and NUL.
    name = _CONTROL_CHARS_RE.sub("", name)

    # Strip any remaining path separators that survived normalisation.
    cleaned = "".join(ch for ch in name if ch not in _PATH_SEPARATORS).strip()
    if not cleaned:
        raise InvalidFileName("Filename is empty after sanitization")
    name = cleaned

    # Reject Windows-reserved stems.
    stem, _ = os.path.splitext(name)
    if _is_windows_reserved(stem):
        raise InvalidFileName(f"Filename uses a reserved name: {stem}")

    # Enforce length cap (UTF-8 byte length — matches DB column semantics).
    if len(name.encode("utf-8")) > settings.max_filename_length:
        raise InvalidFileName(
            f"Filename exceeds {settings.max_filename_length} bytes (UTF-8)"
        )

    return name


def get_extension(filename: str) -> str:
    """Return the lowercase extension without the leading dot, or '' if none."""
    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


def validate_extension(filename: str) -> str:
    """
    Return the validated extension (lowercase, no dot).

    Raises ``UnsupportedFileType`` if the extension is not on the whitelist.
    """
    ext = get_extension(filename)
    if not ext:
        raise UnsupportedFileType("File has no extension")
    if ext not in settings.allowed_ext_set:
        raise UnsupportedFileType(f"Extension '{ext}' is not allowed")
    return ext


def validate_mime_type(content_type: Optional[str]) -> str:
    """
    Return the validated MIME type (lowercased) or ``application/octet-stream``
    when the client did not provide one.

    Raises ``UnsupportedFileType`` for explicitly disallowed types.
    """
    if not content_type:
        return "application/octet-stream"
    # Strip parameters like ``; charset=utf-8``.
    primary = content_type.split(";", 1)[0].strip().lower()
    if not primary:
        return "application/octet-stream"
    if primary not in settings.allowed_mime_set:
        raise UnsupportedFileType(f"Content type '{primary}' is not allowed")
    return primary


def content_disposition_filename(name: str) -> str:
    """
    Build a safe ``Content-Disposition`` filename parameter.

    The result contains both a ``filename=`` (ASCII fallback) and a
    ``filename*=`` (RFC 5987 UTF-8) part, which is what modern browsers
    expect for non-ASCII filenames.
    """
    raw_bytes = name.encode("utf-8")
    ascii_fallback = raw_bytes.decode("ascii", "replace").replace("?", "_")
    # Strip quote-breaking characters from the fallback.
    ascii_fallback = "".join(
        ch if ch not in {'"', "\\", "\r", "\n"} else "_" for ch in ascii_fallback
    )
    if not ascii_fallback.strip():
        ascii_fallback = _FALLBACK_NAME
    quoted = urllib.parse.quote(raw_bytes, safe="")
    return f'filename="{ascii_fallback}"; filename*=UTF-8\'\'{quoted}'

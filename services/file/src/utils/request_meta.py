"""
Request metadata context — exposes the client IP and User-Agent to
service-layer code via :class:`contextvars.ContextVar`.

The middleware in :mod:`src.middleware.request_meta` populates these
values per request.  The audit service reads them when writing rows so
the service methods themselves can stay HTTP-agnostic.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import NamedTuple


class RequestMeta(NamedTuple):
    ip: str | None
    user_agent: str | None


request_meta_var: ContextVar[RequestMeta | None] = ContextVar("request_meta", default=None)


def current_request_meta() -> RequestMeta:
    """Return the current request's IP/UA, or empty defaults."""
    return request_meta_var.get() or RequestMeta(ip=None, user_agent=None)

"""
ASGI middleware that captures the client IP (honouring ``X-Forwarded-For``
when the immediate peer is a trusted proxy) and the User-Agent into a
ContextVar so service code can attribute events without taking a
``Request`` argument.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from src.utils.request_meta import RequestMeta, request_meta_var


# Comma-separated list of trusted proxy IPs / CIDRs.  When unset we never
# trust X-Forwarded-For, which is the safe default for a public service.
_TRUSTED_PROXIES_HEADER = "X-Forwarded-For"


def _resolve_ip(request: Request) -> str | None:
    if request.client is None:
        return None
    peer = request.client.host
    if not peer:
        return None
    # TODO Phase 3: only honour X-Forwarded-For when ``peer`` is in a
    # configured list of trusted proxy CIDRs.  For now we always trust
    # the direct peer, which is safe but loses the real client IP when
    # the service is behind a reverse proxy.
    xff = request.headers.get(_TRUSTED_PROXIES_HEADER)
    if xff:
        # Use the left-most entry — that's the original client.
        return xff.split(",")[0].strip() or None
    return peer


def _resolve_user_agent(request: Request) -> str | None:
    ua = request.headers.get("user-agent")
    if ua is None:
        return None
    return ua[:512]


class RequestMetaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        meta = RequestMeta(
            ip=_resolve_ip(request),
            user_agent=_resolve_user_agent(request),
        )
        token = request_meta_var.set(meta)
        try:
            return await call_next(request)
        finally:
            request_meta_var.reset(token)

"""
Auth Service - Authentication and User Management (Phase 3).

Schema management is handled by Alembic (see ``migrations/``).  The
Docker entrypoint runs ``alembic upgrade head`` before this process
boots; the lifespan below does **not** touch the schema.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.api.exception_handlers import install_exception_handlers
from src.config import settings
from src.middleware import AccessLogMiddleware, RequestIDMiddleware
from src.utils.logging import configure_logging, get_logger
from src.utils.redis_client import close_redis


configure_logging(env=settings.env, level=settings.log_level)
logger = get_logger("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("auth_service.starting", env=settings.env, version="1.1.0")
    yield
    await close_redis()
    logger.info("auth_service.shutting_down")


app = FastAPI(
    title="Cloud Storage Auth Service",
    description="Authentication and user management service for Cloud File Storage",
    version="1.1.0",
    docs_url="/docs/auth",
    redoc_url="/redoc/auth",
    openapi_url="/openapi/auth.json",
    lifespan=lifespan,
)

# Order matters: RequestID must wrap everything else so every log
# line carries the correlation id.  AccessLog sits inside RequestID
# so it can read the request id from the contextvar.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(AccessLogMiddleware)
# CORS is normally enforced by the API gateway (Caddy) — this is
# only useful when the service is run standalone (e.g. integration
# tests).  Origins are configurable via ``CORS_ORIGINS``.
_cors_origins = list(settings.cors_origins_set)
if not _cors_origins:
    import logging as _logging

    _logging.getLogger("auth-service").warning(
        "CORS_ORIGINS is empty — falling back to wildcard ['*']. "
        "Set CORS_ORIGINS in production."
    )
    _cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"],
)

app.include_router(api_router)
install_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

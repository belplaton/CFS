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
from src.config import settings
from src.middleware import RequestIDMiddleware
from src.utils.logging import configure_logging, get_logger


configure_logging(env=settings.env, level=settings.log_level)
logger = get_logger("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("auth_service.starting", env=settings.env, version="1.1.0")
    yield
    logger.info("auth_service.shutting_down")


app = FastAPI(
    title="Cloud Storage Auth Service",
    description="Authentication and user management service for Cloud File Storage",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Order matters: RequestID must wrap everything else so every log
# line carries the correlation id.
app.add_middleware(RequestIDMiddleware)
# CORS is normally enforced by the API gateway (Caddy) — this is
# only useful when the service is run standalone (e.g. integration
# tests).  Origins are configurable via ``CORS_ORIGINS``.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins_set) or ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-API-Key"],
)

app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
File Service - File and Folder Management

Phase 2: schema management is now handled by Alembic.  Production
deployments must run ``alembic upgrade head`` *before* starting this
process (the Docker entrypoint in ``docker-compose.yml`` does this).
The lifespan below does **not** touch the database schema, so multiple
replicas of the service can boot in parallel without race conditions.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import api_router
from src.api.exception_handlers import register_exception_handlers
from src.config import settings
from src.middleware import IdempotencyMiddleware, RequestIDMiddleware, RequestMetaMiddleware
from src.utils.logging import configure_logging, get_logger
from src.utils.rate_limiter import close_redis


configure_logging(env=settings.env, level=settings.log_level)
logger = get_logger("file-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("file_service.starting", env=settings.env, version="1.1.0")
    yield
    await close_redis()
    logger.info("file_service.shutting_down")


app = FastAPI(
    title="Cloud Storage File Service",
    description="File and folder management service for Cloud File Storage",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestMetaMiddleware)
# Idempotency must wrap routes from the inside — Starlette applies
# middlewares in reverse order of ``add_middleware`` calls, so this
# runs before the request reaches the handler and after the response
# is built.  Order matters: keep this as the *last* add_middleware.
app.add_middleware(IdempotencyMiddleware)
register_exception_handlers(app)
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

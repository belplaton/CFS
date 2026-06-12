from __future__ import annotations

import os
import socket
from typing import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

os.environ.setdefault("ENV", "development")
os.environ.setdefault("JWT_SECRET", "pytest-auth-secret")
os.environ.setdefault("SERVICE_API_KEY", "pytest-auth-service-key")

_DB_URL = os.environ.get("DATABASE_URL", "")
USE_DIRECT_DB = "localhost:5432" not in _DB_URL and "postgresql+asyncpg://" in _DB_URL

if not USE_DIRECT_DB:
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://placeholder:placeholder@localhost:5432/placeholder",
    )

from src.models import Base, get_db  # noqa: E402
from src.main import app  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


def _can_start_docker() -> bool:
    if USE_DIRECT_DB:
        return False
    if os.environ.get("SKIP_TESTCONTAINERS") == "1":
        return False
    try:
        with socket.create_connection(("127.0.0.1", 2375), timeout=0.5):
            return True
    except OSError:
        pass
    try:
        with socket.create_connection(("127.0.0.1", 2376), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def postgres_container(request):
    if not _can_start_docker():
        pytest.skip("Docker is not available; testcontainers skipped")
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:15-alpine")
    container.start()
    request.addfinalizer(container.stop)
    return container


@pytest.fixture(scope="session")
def database_url(postgres_container) -> str:
    raw = postgres_container.get_connection_url()
    if raw.startswith("postgresql+asyncpg://"):
        return raw
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise RuntimeError(f"Unexpected DB URL scheme: {raw}")


@pytest_asyncio.fixture
async def test_engine(request):
    """Per-test engine to avoid event loop mismatches with asyncpg."""
    if USE_DIRECT_DB:
        url = os.environ["DATABASE_URL"]
    else:
        container = request.getfixturevalue("postgres_container")
        raw = container.get_connection_url()
        url = raw if raw.startswith("postgresql+asyncpg://") else raw.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url, echo=False, poolclass=pool.NullPool)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    await engine.dispose()


@pytest_asyncio.fixture
async def override_get_db(test_engine):
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def _override() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture(autouse=True)
async def _flush_rate_limits():
    """Clear rate-limit keys from Redis between tests."""
    yield
    try:
        from src.utils.redis_client import get_redis
        redis = get_redis()
        keys = await redis.keys("rl:auth:*")
        if keys:
            await redis.delete(*keys)
    except Exception:  # noqa: BLE001
        pass


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

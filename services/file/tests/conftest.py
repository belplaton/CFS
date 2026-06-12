"""
Pytest configuration and fixtures for File Service (Phase 1).

Database
--------
We use ``testcontainers`` to spin up a real PostgreSQL instance per test
session. This matches the production dialect (UUID, JSONB, advisory locks,
``gen_random_uuid()`` from ``pgcrypto``) and catches issues that the
older SQLite fixture silently let through.

MinIO
-----
A small in-memory fake (``FakeMinioStorage``) stands in for MinIO. Each
test gets its own empty store via the ``fake_minio`` fixture.
"""

from __future__ import annotations

# Set required env vars BEFORE importing anything from ``src`` so that
# ``Settings`` validates correctly when it is first instantiated.
import os

os.environ.setdefault("ENV", "development")
os.environ.setdefault("JWT_SECRET", "pytest-secret-key-do-not-use-in-prod")
os.environ.setdefault("SERVICE_API_KEY", "pytest-service-key-do-not-use-in-prod")
# Placeholder URL — the real engine is built per-test by ``test_engine``
# using the testcontainers connection string. We still need *something*
# here so that ``models.__init__`` does not crash on import.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://placeholder:placeholder@localhost:5432/placeholder",
)

import socket
import uuid
from typing import AsyncIterator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import get_settings
from src.main import app
from src.models import Base, get_db
from src.utils import minio_client as minio_module
from src.utils.dependencies import get_current_user_id
from tests.helpers import USER_ALICE

# Make sure no cached settings leak from a previous test process.
get_settings.cache_clear()


# ==================== PostgreSQL via testcontainers ====================


def _can_start_docker() -> bool:
    """Skip testcontainers gracefully when Docker is not available."""
    if os.environ.get("SKIP_TESTCONTAINERS") == "1":
        return False
    try:
        with socket.create_connection(("127.0.0.1", 2375), timeout=0.5):
            return True
    except OSError:
        pass
    # Also accept the default Docker Desktop named pipe on Windows.
    try:
        with socket.create_connection(("127.0.0.1", 2376), timeout=0.5):
            return True
    except OSError:
        return False


@pytest.fixture(scope="session")
def postgres_container(request):
    """Start a PostgreSQL testcontainer for the session, or skip."""
    if not _can_start_docker():
        pytest.skip("Docker is not available; testcontainers skipped")
    from testcontainers.postgres import PostgresContainer

    container = PostgresContainer("postgres:15-alpine")
    container.start()
    request.addfinalizer(container.stop)
    return container


@pytest.fixture(scope="session")
def database_url(postgres_container) -> str:
    """Async URL for the running Postgres container."""
    raw = postgres_container.get_connection_url()
    # The container returns a sync URL like ``postgresql://...``; asyncpg
    # needs the ``postgresql+asyncpg://`` scheme.
    if raw.startswith("postgresql+asyncpg://"):
        return raw
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    raise RuntimeError(f"Unexpected DB URL scheme: {raw}")


# ==================== Engine (session-scoped) ====================


@pytest_asyncio.fixture(scope="session")
async def test_engine(database_url):
    """Session-scoped async engine with schema bootstrapped."""
    engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncIterator[AsyncSession]:
    """A transactional session that rolls back at the end of the test."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ==================== FastAPI dependency overrides ====================


@pytest_asyncio.fixture
async def override_get_db(test_engine):
    """Route ``get_db`` to the test engine, with per-request isolation."""
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
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


def _make_user_override(user_id: UUID):
    async def _override() -> UUID:
        return user_id

    return _override


@pytest_asyncio.fixture
async def override_auth():
    """Default auth override — authenticated as USER_ALICE."""
    app.dependency_overrides[get_current_user_id] = _make_user_override(USER_ALICE)
    try:
        yield USER_ALICE
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)


def switch_user(user_id: UUID) -> None:
    app.dependency_overrides[get_current_user_id] = _make_user_override(user_id)


# ==================== MinIO fake ====================


class FakeMinioStorage:
    """Tiny in-memory stand-in for MinIO."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    @staticmethod
    def _key(bucket: str, name: str) -> str:
        return f"{bucket}/{name}"

    def put(self, bucket: str, key: str, data: bytes, content_type: str) -> None:
        self.objects[self._key(bucket, key)] = data

    def get(self, bucket: str, key: str) -> bytes | None:
        return self.objects.get(self._key(bucket, key))

    def remove(self, bucket: str, key: str) -> None:
        self.objects.pop(self._key(bucket, key), None)

    def move(self, bucket: str, src: str, dst: str, content_type: str) -> None:
        full = self._key(bucket, src)
        if full in self.objects:
            self.objects[self._key(bucket, dst)] = self.objects.pop(full)


@pytest.fixture
def fake_minio(monkeypatch):
    storage = FakeMinioStorage()

    monkeypatch.setattr(minio_module, "get_minio_client", lambda: storage)
    monkeypatch.setattr(
        minio_module,
        "put_bytes",
        lambda bucket, key, data, content_type="application/octet-stream": storage.put(
            bucket, key, data, content_type
        ),
    )
    monkeypatch.setattr(
        minio_module,
        "remove",
        lambda bucket, key: storage.remove(bucket, key),
    )
    monkeypatch.setattr(
        minio_module,
        "move",
        lambda bucket, src, dst, content_type="application/octet-stream": storage.move(
            bucket, src, dst, content_type
        ),
    )
    monkeypatch.setattr(
        minio_module,
        "get_stream",
        lambda bucket, key, chunk_size=1024 * 1024: iter(
            [storage.get(bucket, key) or b""]
        ),
    )
    monkeypatch.setattr(
        minio_module,
        "presigned_get_url",
        lambda bucket, key, expires=None: f"http://minio.test/{bucket}/{key}",
    )
    monkeypatch.setattr(
        minio_module,
        "stat_size",
        lambda bucket, key: len(storage.get(bucket, key) or b""),
    )
    monkeypatch.setattr(
        minio_module,
        "files_object_key",
        lambda user_id, ext: (
            f"{user_id}/files/{uuid.uuid4()}{('.' + ext) if ext else ''}"
        ),
    )
    monkeypatch.setattr(
        minio_module,
        "trash_object_key",
        lambda user_id, ext: (
            f"{user_id}/trash/{uuid.uuid4()}{('.' + ext) if ext else ''}"
        ),
    )
    return storage


# ==================== Async HTTP client ====================


@pytest_asyncio.fixture
async def async_client(
    override_get_db, override_auth, fake_minio
) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ==================== JWT helpers for auth tests ====================
# ``make_jwt``, ``USER_ALICE``, ``USER_BOB`` are re-exported from
# ``tests.helpers`` at the top of this file.

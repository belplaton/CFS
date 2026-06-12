"""
File Service — SQLAlchemy models package (Phase 2: SQLAlchemy 2.0 style).

The ``Base`` is a ``DeclarativeBase`` subclass and every model uses
``Mapped[...]`` annotations + ``mapped_column(...)``. Phase 2 introduces
Alembic and removes ``create_all`` from production.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


engine = create_async_engine(
    settings.database_url,
    echo=settings.env.lower() == "development",
    pool_pre_ping=True,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
# Re-export under a friendlier name — the scheduler module needs an
# explicit factory to run outside the FastAPI request lifecycle.
async_session_factory = async_session


async def get_db():
    """FastAPI dependency that yields an ``AsyncSession`` per request."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Ensure ``pgcrypto`` extension and create the schema via ``create_all``.

    .. warning::
        This helper is intended **only for tests** (and other ephemeral
        environments).  Production schema management is handled by
        Alembic — run ``alembic upgrade head`` from ``services/file``
        before starting the service, or let the Docker entrypoint do it.
    """
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.run_sync(Base.metadata.create_all)


async def run_migrations() -> None:
    """
    Apply pending Alembic migrations programmatically.

    Use this from the lifespan if you want migrations to be applied
    automatically on application startup (default: NOT — see
    ``main.py``).  Production deployments should prefer the explicit
    ``alembic upgrade head`` step in the Docker entrypoint, which
    keeps schema changes auditable and reviewable.
    """
    from alembic import command
    from alembic.config import Config

    cfg = Config(str(_PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_PROJECT_ROOT / "migrations"))

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, command.upgrade, cfg, "head")


# Model imports must come AFTER ``Base`` is defined and BEFORE ``init_db``
# is called, so that the metadata is populated.
from src.models.audit_log import AuditLog  # noqa: E402,F401
from src.models.file import File  # noqa: E402,F401
from src.models.folder import Folder  # noqa: E402,F401

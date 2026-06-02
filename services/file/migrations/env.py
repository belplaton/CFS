"""
Alembic environment for the file service (async, asyncpg).

The connection URL is read from, in order of priority:

1. ``alembic.ini`` ``sqlalchemy.url`` (if non-empty);
2. ``ALEMBIC_DATABASE_URL`` environment variable;
3. ``settings.database_url`` (loaded by ``src.config``).

Models are imported eagerly so that ``Base.metadata`` is populated for
autogenerate support.  Make sure the ``src`` package is importable — the
``prepend_sys_path = .`` directive in ``alembic.ini`` plus running alembic
from the project root (``cd services/file && alembic ...``) is sufficient.
"""
import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Ensure ``src`` package is importable when alembic is invoked from
# anywhere other than the project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.config import settings  # noqa: E402
from src.models import Base  # noqa: E402
import src.models  # noqa: E402,F401  (register all model classes on Base.metadata)

config = context.config

# Resolve ``sqlalchemy.url``: ini -> env -> settings.
_ini_url = (config.get_main_option("sqlalchemy.url") or "").strip()
_env_url = os.environ.get("ALEMBIC_DATABASE_URL", "").strip()
if _ini_url:
    resolved_url = _ini_url
elif _env_url:
    resolved_url = _env_url
else:
    resolved_url = settings.database_url
config.set_main_option("sqlalchemy.url", resolved_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without DBAPI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async Engine and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

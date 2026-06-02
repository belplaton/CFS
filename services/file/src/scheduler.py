"""
APScheduler bootstrap (Phase 4.2).

A single ``BlockingScheduler`` (or ``AsyncIOScheduler``) is started
in the FastAPI lifespan and stopped on shutdown.  We deliberately
do not import :mod:`src.services.trash_cleanup_service` at module
load time — the scheduler wires the job only when
``settings.trash_cleanup_enabled`` is true, so unit tests can
import this module without a DB engine.
"""
from __future__ import annotations

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import settings
from src.utils.logging import get_logger


logger = get_logger(__name__)


_scheduler: Optional[AsyncIOScheduler] = None


def build_scheduler() -> Optional[AsyncIOScheduler]:
    """
    Build and start the scheduler, returning the running instance.

    Returns ``None`` when the cleanup job is disabled — callers must
    handle the ``None`` case so tests can opt out cleanly.
    """
    global _scheduler
    if not settings.trash_cleanup_enabled:
        logger.info("scheduler.disabled", hint="trash_cleanup_enabled=False")
        return None

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        _run_trash_cleanup,
        trigger=CronTrigger.from_crontab(settings.trash_cleanup_cron),
        id="trash_cleanup",
        name="Trash TTL cleanup",
        replace_existing=True,
        # Multiple replicas can race; the DELETE is idempotent so
        # tolerating a duplicate run is cheaper than adding a leader
        # lock here.
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "scheduler.started",
        cron=settings.trash_cleanup_cron,
        retention_days=settings.trash_retention_days,
    )
    return scheduler


async def shutdown_scheduler() -> None:
    """Stop the scheduler and release its thread."""
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    except Exception:  # noqa: BLE001
        logger.exception("scheduler.shutdown_failed")
    finally:
        _scheduler = None
        logger.info("scheduler.stopped")


async def _run_trash_cleanup() -> None:
    """
    Job body: open a fresh session, run one cleanup pass, commit.

    We intentionally do *not* take the FastAPI ``get_db`` dependency
    here — the scheduler is a background component and must own its
    own session.
    """
    from src.models import async_session_factory
    from src.services.trash_cleanup_service import TrashCleanupService

    try:
        async with async_session_factory() as session:
            async with session.begin():
                svc = TrashCleanupService(session)
                files, folders = await svc.run_once()
                logger.info(
                    "trash.cleanup.done",
                    files_deleted=files,
                    folders_deleted=folders,
                )
    except Exception:  # noqa: BLE001
        logger.exception("trash.cleanup.failed")

"""
Trash TTL cleanup (Phase 4.2).

Hard-deletes any file/folder that has been in the trash for longer
than ``settings.trash_retention_days``.  Runs as a long-lived
scheduled job started by :mod:`src.scheduler.bootstrap`.

Design notes
------------
* **Paged.**  Each tick deletes up to ``BATCH_SIZE`` rows; the loop
  continues until the table is empty for the current ``cutoff``.
  This bounds transaction size and keeps the lock window short.
* **Best-effort MinIO.**  A failed ``remove_object`` is logged but
  does not stop the DB delete — the DB is the source of truth, the
  bucket is just storage.  Orphans are cleaned up by a separate
  reaper (Phase 5).
* **Idempotent.**  If the job is re-run before the next tick, the
  same rows match the cutoff again and the DELETE is a no-op.
* **Single process per cluster.**  We do not implement leader
  election here.  In a multi-replica deployment enable a Redis
  lock around the job or wire APScheduler's ``coalesce=True`` and
  tolerate duplicate work — the DB delete is idempotent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.folder import Folder
from src.repositories.file import FileRepository
from src.repositories.folder import FolderRepository
from src.services import audit_service
from src.services.audit_service import SYSTEM_ACTOR_ID
from src.utils import minio_client
from src.utils.logging import get_logger


logger = get_logger(__name__)


BATCH_SIZE = 500


class TrashCleanupService:
    """Stateless service — caller provides the ``AsyncSession``."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def cutoff(now: datetime | None = None) -> datetime:
        """
        Return the ``deleted_at`` threshold for the current tick.

        ``now`` is parameterised so tests can pin the wall clock.
        """
        moment = now or datetime.now(timezone.utc)
        return moment - timedelta(days=settings.trash_retention_days)

    async def run_once(
        self,
        *,
        now: datetime | None = None,
        batch_size: int = BATCH_SIZE,
    ) -> Tuple[int, int]:
        """
        Run one cleanup pass.

        Returns ``(files_deleted, folders_deleted)``.
        """
        cutoff = self.cutoff(now)
        f_total = 0
        d_total = 0

        # ---- files ---------------------------------------------------
        while True:
            rows = list(
                await FileRepository.list_trashed_before(
                    self.db, cutoff, limit=batch_size
                )
            )
            if not rows:
                break
            for f in rows:
                try:
                    minio_client.remove(settings.minio_bucket, f.minio_object_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "trash.cleanup.minio_failed",
                        file_id=str(f.id),
                        key=f.minio_object_id,
                        error=str(exc),
                    )
                await self.db.delete(f)
            await self.db.flush()
            f_total += len(rows)
            await audit_service.record_event(
                self.db,
                actor_id=SYSTEM_ACTOR_ID,
                event="trash.expired",
                target_id=None,
                target_kind="batch",
                extra={"count": len(rows), "kind": "file"},
            )
            # Looping past the same ``id`` in subsequent ticks is
            # safe — the WHERE clause filters out the now-flagged
            # rows — but we still bail if the batch came back short
            # to avoid an infinite loop on a single stuck row.
            if len(rows) < batch_size:
                break

        # ---- folders -------------------------------------------------
        while True:
            rows = list(
                await FolderRepository.list_trashed_before(
                    self.db, cutoff, limit=batch_size
                )
            )
            if not rows:
                break
            folder_ids = [f.id for f in rows]
            # Hard-delete the folder rows.  Files inside the cascade
            # were already processed by the file pass above.
            await self.db.execute(
                Folder.__table__.delete().where(Folder.id.in_(folder_ids))
            )
            d_total += len(rows)
            await audit_service.record_event(
                self.db,
                actor_id=SYSTEM_ACTOR_ID,
                event="trash.expired",
                target_id=None,
                target_kind="batch",
                extra={"count": len(rows), "kind": "folder"},
            )
            if len(rows) < batch_size:
                break

        if f_total or d_total:
            logger.info(
                "trash.cleanup.tick",
                files_deleted=f_total,
                folders_deleted=d_total,
                retention_days=settings.trash_retention_days,
            )
        return f_total, d_total

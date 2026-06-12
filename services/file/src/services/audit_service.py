"""
Audit service — thin wrapper around the ``audit_logs`` table.

Service-layer code calls :func:`record_event` after a successful
operation.  Failure to write the audit log must never break the user
request, so the insert is wrapped in a try/except and failures are
logged at WARN level for follow-up.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog
from src.utils.logging import get_logger
from src.utils.request_meta import current_request_meta


logger = get_logger(__name__)

SYSTEM_ACTOR_ID = UUID("00000000-0000-0000-0000-000000000000")


async def record_event(
    db: AsyncSession,
    *,
    actor_id: UUID,
    event: str,
    target_id: Optional[UUID] = None,
    target_kind: Optional[str] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> None:
    """
    Append one row to ``audit_logs``.

    ``ip`` and ``user_agent`` are pulled from the request context
    (populated by :class:`src.middleware.request_meta.RequestMetaMiddleware`)
    so service code does not need a ``Request`` argument.

    Best-effort: on DB failure we log and continue.  The user's request
    should not be rejected because we couldn't record an audit row, but
    operators must still see the failure (it indicates a problem worth
    investigating, not user error).
    """
    meta = current_request_meta()
    try:
        db.add(
            AuditLog(
                actor_id=actor_id,
                event=event,
                target_id=target_id,
                target_kind=target_kind,
                ip=meta.ip[:64] if meta.ip else None,
                user_agent=meta.user_agent[:512] if meta.user_agent else None,
                extra=dict(extra) if extra else None,
            )
        )
        await db.flush()
    except SQLAlchemyError:
        logger.warning(
            "audit.write_failed",
            event=event,
            actor_id=str(actor_id),
            target_id=str(target_id) if target_id else None,
            error_type="sqlalchemy",
        )

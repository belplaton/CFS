"""audit log table

Revision ID: 0002_audit_log
Revises: 0001_initial
Create Date: 2026-06-02 00:00:00.000000

Phase 2: record security-relevant events (upload, delete, restore,
move, rename, etc.) in a dedicated table so the service can answer
"who did what when" for incident response and customer support.

We deliberately use UUID for ``actor_id`` even though the auth service
currently issues integer user ids — the conversion happens in
:mod:`src.utils.dependencies`.  This keeps the audit log aligned with
the rest of the schema.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_audit_log"
down_revision: str | None = "0001_initial"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event", sa.String(length=64), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("target_kind", sa.String(length=32), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("extra", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_audit_actor_id", "audit_logs", ["actor_id"])
    op.create_index("idx_audit_event", "audit_logs", ["event"])
    op.create_index("idx_audit_created_at", "audit_logs", ["created_at"])
    op.create_index(
        "idx_audit_target",
        "audit_logs",
        ["target_kind", "target_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_audit_target", table_name="audit_logs")
    op.drop_index("idx_audit_created_at", table_name="audit_logs")
    op.drop_index("idx_audit_event", table_name="audit_logs")
    op.drop_index("idx_audit_actor_id", table_name="audit_logs")
    op.drop_table("audit_logs")

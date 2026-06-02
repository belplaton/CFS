"""initial schema (folders, files)

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02 00:00:00.000000

Phase 2: replaces the implicit ``Base.metadata.create_all`` call with a
real Alembic migration.  The schema here matches what ``create_all``
produced in Phase 1 plus the ``pgcrypto`` extension required by
``gen_random_uuid()``.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ``gen_random_uuid()`` (uuid v4) lives in pgcrypto.  Idempotent.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "folders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "parent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("folders.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index("idx_folders_user_id", "folders", ["user_id"])
    op.create_index("idx_folders_parent_id", "folders", ["parent_id"])
    op.create_index("idx_folders_deleted_at", "folders", ["deleted_at"])

    op.create_table(
        "files",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "folder_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("folders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("minio_object_id", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "deleted_permanently",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=True,
        ),
    )
    op.create_index("idx_files_user_id", "files", ["user_id"])
    op.create_index("idx_files_folder_id", "files", ["folder_id"])
    op.create_index("idx_files_deleted_at", "files", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("idx_files_deleted_at", table_name="files")
    op.drop_index("idx_files_folder_id", table_name="files")
    op.drop_index("idx_files_user_id", table_name="files")
    op.drop_table("files")

    op.drop_index("idx_folders_deleted_at", table_name="folders")
    op.drop_index("idx_folders_parent_id", table_name="folders")
    op.drop_index("idx_folders_user_id", table_name="folders")
    op.drop_table("folders")

    # ``pgcrypto`` is left in place on downgrade — other apps may depend
    # on it and dropping extensions is rarely safe.

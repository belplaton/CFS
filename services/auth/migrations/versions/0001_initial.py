"""initial schema (users, verification_tokens)

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02 00:00:00.000000

Phase 3: replaces the implicit ``Base.metadata.create_all`` call with
a real Alembic migration.  ``users.id`` and
``verification_tokens.user_id`` are UUIDs — the cross-service
contract is that every service identifies a user by the same UUID
issued by Auth.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ``gen_random_uuid()`` (uuid v4) lives in pgcrypto.  Idempotent.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "storage_quota",
            sa.BigInteger(),
            server_default=sa.text("5368709120"),  # 5 GiB
            nullable=False,
        ),
        sa.Column("used_storage", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("totp_secret", sa.String(length=255), nullable=True),
        sa.Column("is_2fa_enabled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "verification_tokens",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("token_type", sa.String(length=50), nullable=False),
        sa.Column("is_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token", name="uq_verification_tokens_token"),
    )
    op.create_index("ix_verification_tokens_user_id", "verification_tokens", ["user_id"])
    op.create_index("ix_verification_tokens_token", "verification_tokens", ["token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_verification_tokens_token", table_name="verification_tokens")
    op.drop_index("ix_verification_tokens_user_id", table_name="verification_tokens")
    op.drop_table("verification_tokens")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # ``pgcrypto`` is left in place on downgrade — other apps may depend
    # on it and dropping extensions is rarely safe.

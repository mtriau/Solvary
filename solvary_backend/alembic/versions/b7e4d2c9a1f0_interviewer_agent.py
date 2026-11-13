"""interviewer agent: users.anthropic_api_key_*, interviewer_turns

Revision ID: b7e4d2c9a1f0
Revises: 9d2f4b7c1e55
Create Date: 2026-11-12

Hand-written: SQLite needs batch mode for the new columns on users.
"""

import sqlalchemy as sa
from alembic import op

revision = "b7e4d2c9a1f0"
down_revision = "9d2f4b7c1e55"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("anthropic_api_key_enc", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("anthropic_api_key_last4", sa.String(length=8), nullable=True)
        )

    op.create_table(
        "interviewer_turns",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("trigger", sa.String(length=16), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("digest", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("silent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("cache_read_input_tokens", sa.Integer(), nullable=True),
        sa.Column("cache_creation_input_tokens", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "ordinal", name="uq_interviewer_turns_session_ordinal"),
    )
    op.create_index(
        "ix_interviewer_turns_session_ordinal",
        "interviewer_turns",
        ["session_id", "ordinal"],
    )


def downgrade() -> None:
    op.drop_index("ix_interviewer_turns_session_ordinal", table_name="interviewer_turns")
    op.drop_table("interviewer_turns")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("anthropic_api_key_last4")
        batch_op.drop_column("anthropic_api_key_enc")

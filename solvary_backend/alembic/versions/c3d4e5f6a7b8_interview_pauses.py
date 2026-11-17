"""interview sessions: pauses

Revision ID: c3d4e5f6a7b8
Revises: b7e4d2c9a1f0
Create Date: 2026-11-17

Hand-written: SQLite needs batch mode to add a NOT NULL column.
"""

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a7b8"
down_revision = "b7e4d2c9a1f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.add_column(
            sa.Column("pauses", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )


def downgrade() -> None:
    with op.batch_alter_table("interview_sessions") as batch_op:
        batch_op.drop_column("pauses")

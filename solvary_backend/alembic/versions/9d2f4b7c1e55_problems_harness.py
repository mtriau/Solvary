"""problems.harness (pytest judge mode)

Revision ID: 9d2f4b7c1e55
Revises: 7c1e2a9b4d10
Create Date: 2026-11-04

"""

import sqlalchemy as sa
from alembic import op

revision = "9d2f4b7c1e55"
down_revision = "7c1e2a9b4d10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("harness", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("problems", "harness")

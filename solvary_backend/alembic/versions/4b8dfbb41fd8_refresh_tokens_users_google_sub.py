"""refresh tokens + users.google_sub

Revision ID: 4b8dfbb41fd8
Revises: acc9c07eb245
Create Date: 2026-07-13 18:21:52.335486

Hand-written (not autogen): the dev DB was polluted by lifespan create_all
before autogenerate ran, and SQLite needs batch mode for the unique
constraint on the new column.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b8dfbb41fd8'
down_revision: Union[str, Sequence[str], None] = 'acc9c07eb245'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("google_sub", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint("uq_users_google_sub", ["google_sub"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_google_sub", type_="unique")
        batch_op.drop_column("google_sub")

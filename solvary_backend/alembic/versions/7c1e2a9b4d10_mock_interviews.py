"""mock interviews: templates, stages, sessions; submissions.interview_session_id; workspaces.kind

Revision ID: 7c1e2a9b4d10
Revises: 4b8dfbb41fd8
Create Date: 2026-11-04 15:00:00

Hand-written: SQLite needs batch mode for the new FK column on submissions.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1e2a9b4d10'
down_revision: Union[str, Sequence[str], None] = '4b8dfbb41fd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_templates",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description_md", sa.Text(), nullable=False),
        sa.Column("format", sa.String(length=20), nullable=False),
        sa.Column("duration_s", sa.Integer(), nullable=False),
        sa.Column("advance", sa.String(length=20), nullable=False),
        sa.Column("pacing", sa.String(length=20), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_templates_slug"), "interview_templates", ["slug"], unique=True)

    op.create_table(
        "interview_stages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("budget_s", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["template_id"], ["interview_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "ordinal", name="uq_interview_stages_template_ordinal"),
        sa.UniqueConstraint("template_id", "problem_id", name="uq_interview_stages_template_problem"),
    )

    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.add_column(
            sa.Column("kind", sa.String(length=20), nullable=False, server_default="standard")
        )

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.String(length=30), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_stage", sa.Integer(), nullable=False),
        sa.Column("unlocked_through", sa.Integer(), nullable=False),
        sa.Column("stage_files", sa.JSON(), nullable=False),
        sa.Column("timeline", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.ForeignKeyConstraint(["template_id"], ["interview_templates.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_interview_sessions_user_created", "interview_sessions", ["user_id", "created_at"])
    op.create_index("ix_interview_sessions_user_status", "interview_sessions", ["user_id", "status"])

    with op.batch_alter_table("submissions") as batch_op:
        batch_op.add_column(sa.Column("interview_session_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_submissions_interview_session",
            "interview_sessions",
            ["interview_session_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_submissions_interview_session", ["interview_session_id", "created_at"]
        )


def downgrade() -> None:
    with op.batch_alter_table("submissions") as batch_op:
        batch_op.drop_index("ix_submissions_interview_session")
        batch_op.drop_constraint("fk_submissions_interview_session", type_="foreignkey")
        batch_op.drop_column("interview_session_id")
    op.drop_index("ix_interview_sessions_user_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_user_created", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    with op.batch_alter_table("workspaces") as batch_op:
        batch_op.drop_column("kind")
    op.drop_table("interview_stages")
    op.drop_index(op.f("ix_interview_templates_slug"), table_name="interview_templates")
    op.drop_table("interview_templates")

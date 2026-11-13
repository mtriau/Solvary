"""
SQLAlchemy ORM table definitions.

These map directly to database tables. They are separate from domain models
in app/models/ — services work with domain models, repositories handle
the conversion between ORM rows and domain objects.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRow(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="user")  # user | admin
    google_sub: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    # Interviewer agent: the user's Anthropic key, Fernet-encrypted (core/secrets.py)
    anthropic_api_key_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    anthropic_api_key_last4: Mapped[str | None] = mapped_column(String(8), nullable=True)


class ProblemRow(Base, TimestampMixin):
    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # easy | medium | hard
    statement_md: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    starter_code: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    function_signature: Mapped[str | None] = mapped_column(String(500), nullable=True)
    judge_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="stdio")
    harness: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_limit_s: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    memory_kb: Mapped[int] = mapped_column(Integer, nullable=False, default=256_000)
    editorial_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    testcases: Mapped[list["TestCaseRow"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )


class TestCaseRow(Base):
    __tablename__ = "testcases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    stdin: Mapped[str] = mapped_column(Text, nullable=False)
    expected_stdout: Mapped[str] = mapped_column(Text, nullable=False)
    checker: Mapped[str] = mapped_column(String(30), nullable=False, default="exact")
    checker_args: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    time_limit_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    problem: Mapped["ProblemRow"] = relationship(back_populates="testcases")

    __table_args__ = (
        Index("ix_testcases_problem_ordinal", "problem_id", "ordinal"),
        UniqueConstraint("problem_id", "ordinal", name="uq_testcases_problem_ordinal"),
    )


class SubmissionRow(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    interview_session_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("interview_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    language: Mapped[str] = mapped_column(String(30), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    verdict: Mapped[str] = mapped_column(String(30), nullable=False, default="queued")
    runtime_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    test_results: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    __table_args__ = (
        Index("ix_submissions_user_created", "user_id", "created_at"),
        Index("ix_submissions_problem_verdict", "problem_id", "verdict"),
        Index("ix_submissions_interview_session", "interview_session_id", "created_at"),
    )


class WorkspaceRow(Base, TimestampMixin):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(30), nullable=False, default="python")
    problem_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("problems.id", ondelete="SET NULL"), nullable=True
    )
    # "standard" | "interview" — interview workspaces are owned by a mock
    # interview session and hidden from the workspaces list
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")

    members: Mapped[list["WorkspaceMemberRow"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    files: Mapped[list["WorkspaceFileRow"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )


class WorkspaceMemberRow(Base):
    __tablename__ = "workspace_members"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # owner | editor | viewer
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    workspace: Mapped["WorkspaceRow"] = relationship(back_populates="members")

    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_members_workspace_user"),
    )


class WorkspaceFileRow(Base, TimestampMixin):
    __tablename__ = "workspace_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    language: Mapped[str | None] = mapped_column(String(30), nullable=True)

    workspace: Mapped["WorkspaceRow"] = relationship(back_populates="files")

    __table_args__ = (
        UniqueConstraint("workspace_id", "path", name="uq_files_workspace_path"),
    )


class DocSnapshotRow(Base):
    __tablename__ = "doc_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    state: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    update_seq: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("ix_doc_snapshots_workspace_created", "workspace_id", "created_at"),
    )


class DocUpdateRow(Base):
    __tablename__ = "doc_updates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "seq", name="uq_doc_updates_workspace_seq"),
    )


class RefreshTokenRow(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (Index("ix_refresh_tokens_user", "user_id"),)


# ── Mock interviews (SOLVARY_INTERVIEWS_DESIGN.md §4) ─────────────


class InterviewTemplateRow(Base, TimestampMixin):
    __tablename__ = "interview_templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    format: Mapped[str] = mapped_column(String(20), nullable=False)  # levels | questions
    duration_s: Mapped[int] = mapped_column(Integer, nullable=False)
    advance: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    pacing: Mapped[str] = mapped_column(String(20), nullable=False, default="coached")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    stages: Mapped[list["InterviewStageRow"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class InterviewStageRow(Base):
    __tablename__ = "interview_stages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_templates.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("problems.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    budget_s: Mapped[int | None] = mapped_column(Integer, nullable=True)

    template: Mapped["InterviewTemplateRow"] = relationship(back_populates="stages")

    __table_args__ = (
        UniqueConstraint("template_id", "ordinal", name="uq_interview_stages_template_ordinal"),
        UniqueConstraint("template_id", "problem_id", name="uq_interview_stages_template_problem"),
    )


class InterviewSessionRow(Base, TimestampMixin):
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    template_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_templates.id", ondelete="RESTRICT"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    language: Mapped[str] = mapped_column(String(30), nullable=False, default="python")
    workspace_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_stage: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unlocked_through: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    stage_files: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    timeline: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    __table_args__ = (
        Index("ix_interview_sessions_user_created", "user_id", "created_at"),
        Index("ix_interview_sessions_user_status", "user_id", "status"),
    )


# ── Interviewer agent (SOLVARY_INTERVIEWER_DESIGN.md §6) ──────────


class InterviewerTurnRow(Base):
    __tablename__ = "interviewer_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # user | assistant
    trigger: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    digest: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    silent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_read_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cache_creation_input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        UniqueConstraint("session_id", "ordinal", name="uq_interviewer_turns_session_ordinal"),
        Index("ix_interviewer_turns_session_ordinal", "session_id", "ordinal"),
    )

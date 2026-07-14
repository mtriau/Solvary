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

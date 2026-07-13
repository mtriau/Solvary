from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

MemberRole = Literal["owner", "editor", "viewer"]


@dataclass
class Workspace:
    id: str
    name: str
    owner_id: str
    language: str = "python"
    problem_id: str | None = None  # set → this workspace is a challenge attempt
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkspaceMember:
    id: str
    workspace_id: str
    user_id: str
    role: MemberRole
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class WorkspaceFile:
    """Server-authoritative file METADATA (design §4). Content lives in the
    CRDT doc's Y.Map keyed by this row's id — never by path, so rename
    preserves content identity."""

    id: str
    workspace_id: str
    path: str
    language: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

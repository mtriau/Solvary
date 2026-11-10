from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, field_validator

MemberRole = Literal["owner", "editor", "viewer"]


# ── Workspaces ─────────────────────────────────────────────────────


class WorkspaceCreate(BaseModel):
    name: str | None = None  # defaults to the problem title for attempts
    language: str = "python"
    problem_id: str | None = None  # set -> challenge attempt (M4)


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    language: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    language: str
    problem_id: str | None
    problem_slug: str | None = None
    problem_title: str | None = None
    my_role: MemberRole
    kind: Literal["standard", "interview"] = "standard"
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        return v if v.tzinfo else v.replace(tzinfo=UTC)


# ── Members ────────────────────────────────────────────────────────


class MemberAdd(BaseModel):
    email: EmailStr
    role: Literal["editor", "viewer"] = "editor"  # owner only via creation


class MemberResponse(BaseModel):
    id: str
    user_id: str
    name: str
    email: EmailStr
    avatar_url: str
    role: MemberRole


# ── Files (metadata only — content flows over the CRDT socket) ────


class FileCreate(BaseModel):
    path: str
    language: str | None = None


class FileRename(BaseModel):
    path: str


class FileResponse(BaseModel):
    id: str
    path: str
    language: str | None

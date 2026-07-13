from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr

MemberRole = Literal["owner", "editor", "viewer"]


# ── Workspaces ─────────────────────────────────────────────────────


class WorkspaceCreate(BaseModel):
    name: str
    language: str = "python"


class WorkspaceUpdate(BaseModel):
    name: str | None = None
    language: str | None = None


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    language: str
    problem_id: str | None
    my_role: MemberRole
    created_at: datetime


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

"""
Mock interviews (SOLVARY_INTERVIEWS_DESIGN.md).

A template is an ordered list of stages; a stage IS a Problem. A session is
one user's timed run through a template — its code lives in a workspace of
kind "interview" (one file per stage in `questions` format, one shared file
in `levels` format), its results are derived from the submissions tagged
with its id, and its clock is server-authoritative.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

InterviewFormat = Literal["levels", "questions"]
AdvancePolicy = Literal["free", "on_submit", "on_accept"]
Pacing = Literal["coached", "strict"]
SessionStatus = Literal["active", "finished", "expired", "abandoned"]


@dataclass
class InterviewTemplate:
    id: str
    slug: str
    title: str
    description_md: str
    format: InterviewFormat
    duration_s: int
    advance: AdvancePolicy = "free"  # levels only
    pacing: Pacing = "coached"
    is_public: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InterviewStage:
    id: str
    template_id: str
    ordinal: int  # 1-based
    problem_id: str
    title: str
    budget_s: int | None = None  # suggested time for this part (pacing coach)


@dataclass
class InterviewSession:
    id: str
    template_id: str
    user_id: str
    language: str
    workspace_id: str | None
    started_at: datetime
    ends_at: datetime
    status: SessionStatus = "active"
    finished_at: datetime | None = None
    current_stage: int = 1
    unlocked_through: int = 1
    # JSON columns: keys are str(ordinal) → workspace file id
    stage_files: dict[str, str] = field(default_factory=dict)
    # [{"stage": int, "at": iso8601}] — appended on start / advance / switch
    timeline: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

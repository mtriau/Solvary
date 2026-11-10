from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.problems import ProblemDetail
from app.schemas.submissions import SubmissionResponse

InterviewFormat = Literal["levels", "questions"]
AdvancePolicy = Literal["free", "on_submit", "on_accept"]
Pacing = Literal["coached", "strict"]
SessionStatus = Literal["active", "finished", "expired", "abandoned"]


# ── Templates ──────────────────────────────────────────────────────


class StageInfo(BaseModel):
    ordinal: int
    title: str
    budget_s: int | None


class TemplateInfo(BaseModel):
    id: str
    slug: str
    title: str
    format: InterviewFormat
    duration_s: int
    advance: AdvancePolicy
    pacing: Pacing


class Score(BaseModel):
    passed: int
    total: int
    percent: int  # 0..100, rounded


class SessionSummary(BaseModel):
    id: str
    template: TemplateInfo
    status: SessionStatus
    language: str
    duration_s: int  # this run's clock (may differ from the template's)
    started_at: datetime
    ends_at: datetime
    finished_at: datetime | None
    server_time: datetime
    score: Score
    time_used_s: int
    stages_reached: int
    stage_count: int
    diagnosis: str | None  # pacing one-liner, None while active


class TemplateSummary(TemplateInfo):
    stages: list[StageInfo]
    last_result: SessionSummary | None = None


class TemplateDetail(TemplateSummary):
    description_md: str


class StageCreate(BaseModel):
    problem_id: str
    title: str
    budget_s: int | None = Field(default=None, ge=60)


class TemplateCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=1, max_length=255)
    description_md: str = ""
    format: InterviewFormat
    duration_s: int = Field(ge=60, le=6 * 3600)
    advance: AdvancePolicy = "free"
    pacing: Pacing = "coached"
    is_public: bool = True
    stages: list[StageCreate] = Field(min_length=1, max_length=12)


# ── Sessions ───────────────────────────────────────────────────────


class SessionStart(BaseModel):
    template_id: str
    language: str = "python"
    # Override the template's clock; stage budgets scale proportionally
    duration_s: int | None = Field(default=None, ge=5 * 60, le=4 * 3600)


class SwitchStage(BaseModel):
    stage: int = Field(ge=1)


class StageResult(BaseModel):
    submissions: int
    best_submission_id: str | None
    best_verdict: str | None
    best_passed: int
    best_total: int
    time_spent_s: int


class StageView(BaseModel):
    ordinal: int
    title: str
    budget_s: int | None
    locked: bool
    file_id: str | None
    deadline_at: datetime | None  # strict pacing only
    problem: ProblemDetail | None  # None while locked
    editorial_md: str | None  # review only
    result: StageResult


class TimelineEntry(BaseModel):
    stage: int
    at: datetime


class SessionDetail(SessionSummary):
    workspace_id: str | None
    current_stage: int
    unlocked_through: int
    stages: list[StageView]
    timeline: list[TimelineEntry]


class SessionReview(SessionDetail):
    submissions: list[SubmissionResponse]

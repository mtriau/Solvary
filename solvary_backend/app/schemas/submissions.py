from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, field_validator

Verdict = Literal[
    "queued",
    "running",
    "accepted",
    "wrong_answer",
    "tle",
    "mle",
    "runtime_error",
    "compile_error",
    "internal_error",
]


class SubmissionCreate(BaseModel):
    problem_id: str
    language: str
    code: str
    workspace_id: str | None = None
    interview_session_id: str | None = None  # mock interview (counts toward its score)


class TestResult(BaseModel):
    ordinal: int
    status: str
    runtime_ms: int | None = None
    memory_kb: int | None = None


class SubmissionResponse(BaseModel):
    id: str
    user_id: str
    problem_id: str
    workspace_id: str | None
    interview_session_id: str | None = None
    language: str
    verdict: Verdict
    runtime_ms: int | None
    memory_kb: int | None
    passed: int
    total: int
    test_results: list[TestResult]
    created_at: datetime

    @field_validator("created_at")
    @classmethod
    def _utc(cls, v: datetime) -> datetime:
        # SQLite hands back naive datetimes; without a zone the browser parses
        # the ISO string as local time and interview offsets shift by hours.
        return v if v.tzinfo else v.replace(tzinfo=UTC)


class SubmissionDetail(SubmissionResponse):
    code: str

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

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
    language: str
    verdict: Verdict
    runtime_ms: int | None
    memory_kb: int | None
    passed: int
    total: int
    test_results: list[TestResult]
    created_at: datetime


class SubmissionDetail(SubmissionResponse):
    code: str

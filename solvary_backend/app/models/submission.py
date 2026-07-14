from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

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


@dataclass
class Submission:
    id: str
    user_id: str
    problem_id: str
    language: str
    code: str
    workspace_id: str | None = None
    verdict: Verdict = "queued"
    runtime_ms: int | None = None
    memory_kb: int | None = None
    passed: int = 0
    total: int = 0
    # per-test {ordinal, status, runtime_ms, memory_kb}; appended incrementally
    # by the worker — this is what makes SSE replay-then-follow possible
    test_results: list[dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

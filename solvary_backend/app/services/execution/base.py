"""
Execution provider abstraction — mirrors the LLM provider pattern.

Division of labor (SOLVARY_DESIGN.md §6):
  - The EXECUTOR runs code and yields raw per-case results (stdout, timing,
    resource-failure statuses). It is the isolation boundary for untrusted code.
  - The WORKER (app/services/queue/worker.py) applies checkers to decide
    pass/fail, computes the aggregate verdict, persists incrementally, and
    publishes client-facing events. Executors never emit `verdict` events.

Per-case events are best effort: an executor that batches (e.g. Judge0) and
emits coarser progress is contract-conformant; only queued → … ordering and a
terminal outcome are guaranteed.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Literal

EventKind = Literal["queued", "compiling", "case_started", "case_result", "verdict", "error"]


@dataclass
class ExecCase:
    ordinal: int
    stdin: str
    expected_stdout: str
    checker: str = "exact"
    checker_args: dict = field(default_factory=dict)
    is_sample: bool = False
    weight: int = 1
    time_limit_s: float | None = None
    memory_kb: int | None = None


@dataclass
class ExecJob:
    id: str  # sub_… (judge) or run_… (ad-hoc)
    user_id: str
    language: str
    code: str
    mode: Literal["run", "judge"]
    cases: list[ExecCase] = field(default_factory=list)  # empty for ad-hoc run
    stdin: str = ""  # ad-hoc run input
    time_limit_s: float = 5.0
    memory_kb: int = 256_000
    # pytest judging (see pytest_harness.py): run the provided suite in one go
    harness: dict | None = None


@dataclass
class ExecEvent:
    """A single event in an execution stream (also the SSE payload shape)."""

    kind: EventKind
    ordinal: int | None = None
    status: str | None = None  # per-case: passed/failed/tle/mle/runtime_error
    runtime_ms: int | None = None
    memory_kb: int | None = None
    verdict: str | None = None
    message: str | None = None
    stdout: str | None = None  # raw output; stripped from hidden cases client-side
    passed: int | None = None  # verdict events: aggregate counts
    total: int | None = None

    def to_public_dict(self, hidden_ordinals: set[int] | None = None) -> dict:
        """Client-facing shape; never leak hidden-case stdout."""
        d = {k: v for k, v in self.__dict__.items() if v is not None}
        if (
            hidden_ordinals
            and self.ordinal is not None
            and self.ordinal in hidden_ordinals
        ):
            d.pop("stdout", None)
        return d


class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, job: ExecJob) -> AsyncIterator[ExecEvent]:
        """Run the job, yielding events. Must not emit `verdict` events."""
        ...

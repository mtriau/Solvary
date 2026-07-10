import uuid
from collections.abc import AsyncIterator

from app.config import Settings
from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.problem import SUPPORTED_LANGUAGES
from app.models.submission import Submission
from app.models.user import User
from app.repositories.problem_repository import ProblemRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.schemas.common import PaginatedResponse
from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionResponse,
    TestResult,
)
from app.services.execution.base import ExecCase, ExecJob
from app.services.queue.runtime import ExecutionRuntime

_TERMINAL_VERDICTS = {
    "accepted",
    "wrong_answer",
    "tle",
    "mle",
    "runtime_error",
    "compile_error",
    "internal_error",
}


class SubmissionService:
    def __init__(
        self,
        submission_repo: SubmissionRepository,
        problem_repo: ProblemRepository,
        testcase_repo: TestCaseRepository,
        runtime: ExecutionRuntime,
        settings: Settings,
    ) -> None:
        self._submission_repo = submission_repo
        self._problem_repo = problem_repo
        self._testcase_repo = testcase_repo
        self._runtime = runtime
        self._settings = settings

    # ── create → enqueue ───────────────────────────────────────────

    async def create(self, user: User, data: SubmissionCreate) -> SubmissionResponse:
        if data.language not in SUPPORTED_LANGUAGES:
            supported = ", ".join(SUPPORTED_LANGUAGES)
            raise BadRequestException(
                f"Unsupported language '{data.language}' (supported: {supported})"
            )
        if len(data.code.encode()) > self._settings.execution_max_code_bytes:
            raise BadRequestException(
                f"Code exceeds {self._settings.execution_max_code_bytes} bytes"
            )

        problem = await self._problem_repo.get_by_id(data.problem_id)
        if not problem:
            raise NotFoundException(f"Problem {data.problem_id} not found")

        cases = await self._testcase_repo.list_by_problem(problem.id)
        if not cases:
            raise BadRequestException("Problem has no test cases; cannot judge")

        submission = Submission(
            id=f"sub_{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            problem_id=problem.id,
            workspace_id=data.workspace_id,
            language=data.language,
            code=data.code,
            total=len(cases),
        )
        await self._submission_repo.create(submission)

        # Samples first (§6.3): on failure, remaining hidden cases are
        # skipped while remaining samples still run — ordering makes that
        # a simple stream cutoff in the worker.
        ordered = sorted(cases, key=lambda c: (not c.is_sample, c.ordinal))
        job = ExecJob(
            id=submission.id,
            user_id=user.id,
            language=data.language,
            code=data.code,
            mode="judge",
            cases=[
                ExecCase(
                    ordinal=c.ordinal,
                    stdin=c.stdin,
                    expected_stdout=c.expected_stdout,
                    checker=c.checker,
                    checker_args=c.checker_args,
                    is_sample=c.is_sample,
                    weight=c.weight,
                    time_limit_s=c.time_limit_s,
                    memory_kb=c.memory_kb,
                )
                for c in ordered
            ],
            time_limit_s=problem.time_limit_s,
            memory_kb=problem.memory_kb,
        )
        await self._runtime.queue.enqueue(job)
        return self._to_response(submission)

    # ── reads ──────────────────────────────────────────────────────

    async def get(self, user: User, submission_id: str) -> SubmissionDetail:
        submission = await self._get_authorized(user, submission_id)
        return self._to_detail(submission)

    async def list_mine(
        self,
        user: User,
        problem_id: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedResponse[SubmissionResponse]:
        submissions, next_cursor = await self._submission_repo.list_paginated(
            user_id=user.id, problem_id=problem_id, cursor=cursor, limit=limit
        )
        return PaginatedResponse(
            items=[self._to_response(s) for s in submissions],
            next_cursor=next_cursor,
        )

    # ── SSE: replay-then-follow (§6.4) ─────────────────────────────

    async def stream_events(self, user: User, submission_id: str) -> AsyncIterator[dict]:
        submission = await self._get_authorized(user, submission_id)

        # 1) Replay from the row (worker persists incrementally)
        replayed_ordinals: set[int] = set()
        yield {"kind": "queued"}
        if submission.verdict != "queued":
            for result in submission.test_results:
                replayed_ordinals.add(result["ordinal"])
                yield {
                    "kind": "case_result",
                    "ordinal": result["ordinal"],
                    "status": result["status"],
                    "runtime_ms": result.get("runtime_ms"),
                    "memory_kb": result.get("memory_kb"),
                }
        if submission.verdict in _TERMINAL_VERDICTS:
            yield {
                "kind": "verdict",
                "verdict": submission.verdict,
                "passed": submission.passed,
                "total": submission.total,
                "runtime_ms": submission.runtime_ms,
                "memory_kb": submission.memory_kb,
            }
            return

        # 2) Follow the live channel, deduplicating replayed case events
        async for event in self._runtime.broker.subscribe(submission_id):
            if (
                event.get("kind") in ("case_result", "case_started")
                and event.get("ordinal") in replayed_ordinals
            ):
                continue
            if event.get("kind") == "queued":
                continue  # already emitted
            yield event

    # ── helpers ────────────────────────────────────────────────────

    async def _get_authorized(self, user: User, submission_id: str) -> Submission:
        submission = await self._submission_repo.get_by_id(submission_id)
        if not submission:
            raise NotFoundException(f"Submission {submission_id} not found")
        if submission.user_id != user.id and user.role != "admin":
            raise ForbiddenException("Not your submission")
        return submission

    @staticmethod
    def _to_response(s: Submission) -> SubmissionResponse:
        return SubmissionResponse(
            id=s.id,
            user_id=s.user_id,
            problem_id=s.problem_id,
            workspace_id=s.workspace_id,
            language=s.language,
            verdict=s.verdict,
            runtime_ms=s.runtime_ms,
            memory_kb=s.memory_kb,
            passed=s.passed,
            total=s.total,
            test_results=[TestResult(**r) for r in s.test_results],
            created_at=s.created_at,
        )

    @staticmethod
    def _to_detail(s: Submission) -> SubmissionDetail:
        return SubmissionDetail(
            id=s.id,
            user_id=s.user_id,
            problem_id=s.problem_id,
            workspace_id=s.workspace_id,
            language=s.language,
            verdict=s.verdict,
            runtime_ms=s.runtime_ms,
            memory_kb=s.memory_kb,
            passed=s.passed,
            total=s.total,
            test_results=[TestResult(**r) for r in s.test_results],
            created_at=s.created_at,
            code=s.code,
        )

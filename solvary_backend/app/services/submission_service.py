import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

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
from app.repositories.workspace_repository import MemberRepository, WorkspaceRepository
from app.schemas.common import PaginatedResponse
from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionDetail,
    SubmissionResponse,
    TestResult,
)
from app.services.execution.base import ExecCase, ExecJob
from app.services.queue.runtime import ExecutionRuntime

if TYPE_CHECKING:  # avoid the import cycle: interview_service imports us
    from app.services.interview_service import InterviewService

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
        workspace_repo: WorkspaceRepository,
        member_repo: MemberRepository,
        runtime: ExecutionRuntime,
        settings: Settings,
        interview_service: "InterviewService | None" = None,
    ) -> None:
        self._interviews = interview_service
        self._submission_repo = submission_repo
        self._problem_repo = problem_repo
        self._testcase_repo = testcase_repo
        self._workspace_repo = workspace_repo
        self._member_repo = member_repo
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
        if problem.judge_mode == "pytest" and data.language != "python":
            raise BadRequestException("This problem is judged with a Python test suite")

        # Mock interview: the session (not the workspace) binds the problem -
        # it must be live and the stage unlocked. Checked first so a locked
        # stage is a 403 regardless of workspace membership.
        if data.interview_session_id:
            if self._interviews is None:
                raise BadRequestException("Interviews are not available")
            await self._interviews.authorize_submission(
                user, data.interview_session_id, data.problem_id, data.workspace_id
            )

        # Workspace-tagged submission (M4 challenge attempt): submitter must
        # be an editor+ member, and the workspace must be bound to this problem
        if data.workspace_id:
            workspace = await self._workspace_repo.get_by_id(data.workspace_id)
            if not workspace:
                raise NotFoundException(f"Workspace {data.workspace_id} not found")
            member = await self._member_repo.get_by_workspace_and_user(
                data.workspace_id, user.id
            )
            if member is None or member.role == "viewer":
                raise ForbiddenException("Submitting requires editor access")
            if not data.interview_session_id and workspace.problem_id != data.problem_id:
                raise BadRequestException("Workspace is not bound to this problem")

        cases = await self._testcase_repo.list_by_problem(problem.id)
        if not cases:
            raise BadRequestException("Problem has no test cases; cannot judge")

        submission = Submission(
            id=f"sub_{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            problem_id=problem.id,
            workspace_id=data.workspace_id,
            interview_session_id=data.interview_session_id,
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
            harness=problem.harness if problem.judge_mode == "pytest" else None,
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

    async def list_for_workspace(
        self,
        user: User,
        workspace_id: str,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedResponse[SubmissionResponse]:
        """All members' submissions in a workspace — the shared attempt history."""
        member = await self._member_repo.get_by_workspace_and_user(workspace_id, user.id)
        if member is None and user.role != "admin":
            raise ForbiddenException("Not a member of this workspace")
        submissions, next_cursor = await self._submission_repo.list_paginated(
            workspace_id=workspace_id, cursor=cursor, limit=limit
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
        if submission.user_id == user.id or user.role == "admin":
            return submission
        # Workspace submissions are visible to every member — pair
        # interviews share one verdict stream (M4)
        if submission.workspace_id:
            member = await self._member_repo.get_by_workspace_and_user(
                submission.workspace_id, user.id
            )
            if member is not None:
                return submission
        raise ForbiddenException("Not your submission")

    @staticmethod
    def _to_response(s: Submission) -> SubmissionResponse:
        return SubmissionResponse(
            id=s.id,
            user_id=s.user_id,
            problem_id=s.problem_id,
            workspace_id=s.workspace_id,
            interview_session_id=s.interview_session_id,
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
            interview_session_id=s.interview_session_id,
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

import uuid

from app.core.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.problem import Problem
from app.models.testcase import TestCase
from app.models.user import User
from app.repositories.problem_repository import ProblemRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.schemas.common import PaginatedResponse
from app.schemas.problems import (
    ProblemCreate,
    ProblemDetail,
    ProblemSummary,
    ProblemUpdate,
    TestCaseAdmin,
    TestCaseCreate,
    TestCaseSample,
)


class ProblemService:
    def __init__(
        self,
        problem_repo: ProblemRepository,
        testcase_repo: TestCaseRepository,
    ) -> None:
        self._problem_repo = problem_repo
        self._testcase_repo = testcase_repo

    # ── public reads ───────────────────────────────────────────────

    async def list_problems(
        self,
        difficulty: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> PaginatedResponse[ProblemSummary]:
        problems, next_cursor = await self._problem_repo.list_paginated(
            difficulty=difficulty, tag=tag, q=q, cursor=cursor, limit=limit
        )
        return PaginatedResponse(
            items=[self._to_summary(p) for p in problems],
            next_cursor=next_cursor,
        )

    async def get_by_slug(self, slug: str, include_private: bool = False) -> ProblemDetail:
        problem = await self._problem_repo.get_by_slug(slug)
        if not problem or (not problem.is_public and not include_private):
            raise NotFoundException(f"Problem '{slug}' not found")
        cases = await self._testcase_repo.list_by_problem(problem.id)
        samples = [
            TestCaseSample(ordinal=c.ordinal, stdin=c.stdin, expected_stdout=c.expected_stdout)
            for c in cases
            if c.is_sample
        ]
        return self._to_detail(problem, samples)

    # ── admin authoring ────────────────────────────────────────────

    async def create(self, data: ProblemCreate, admin: User) -> ProblemDetail:
        existing = await self._problem_repo.get_by_slug(data.slug)
        if existing:
            raise ConflictException(f"A problem with slug '{data.slug}' already exists")

        problem = Problem(
            id=f"prob_{uuid.uuid4().hex[:8]}",
            slug=data.slug,
            title=data.title,
            difficulty=data.difficulty,
            statement_md=data.statement_md,
            tags=data.tags,
            starter_code=data.starter_code,
            function_signature=data.function_signature,
            judge_mode=data.judge_mode,
            harness=data.harness,
            time_limit_s=data.time_limit_s,
            memory_kb=data.memory_kb,
            editorial_md=data.editorial_md,
            is_public=data.is_public,
            created_by=admin.id,
        )
        await self._problem_repo.create(problem)
        return self._to_detail(problem, samples=[])

    async def update(self, problem_id: str, data: ProblemUpdate) -> ProblemDetail:
        problem = await self._problem_repo.get_by_id(problem_id)
        if not problem:
            raise NotFoundException(f"Problem {problem_id} not found")

        for field_name, value in data.model_dump(exclude_unset=True).items():
            setattr(problem, field_name, value)
        await self._problem_repo.update(problem)

        cases = await self._testcase_repo.list_by_problem(problem.id)
        samples = [
            TestCaseSample(ordinal=c.ordinal, stdin=c.stdin, expected_stdout=c.expected_stdout)
            for c in cases
            if c.is_sample
        ]
        return self._to_detail(problem, samples)

    async def list_testcases(self, problem_id: str) -> list[TestCaseAdmin]:
        problem = await self._problem_repo.get_by_id(problem_id)
        if not problem:
            raise NotFoundException(f"Problem {problem_id} not found")
        cases = await self._testcase_repo.list_by_problem(problem_id)
        return [self._to_admin_case(c) for c in cases]

    async def add_testcase(self, problem_id: str, data: TestCaseCreate) -> TestCaseAdmin:
        problem = await self._problem_repo.get_by_id(problem_id)
        if not problem:
            raise NotFoundException(f"Problem {problem_id} not found")

        existing = await self._testcase_repo.list_by_problem(problem_id)
        if any(c.ordinal == data.ordinal for c in existing):
            raise BadRequestException(f"Ordinal {data.ordinal} already exists for this problem")

        case = TestCase(
            id=f"tc_{uuid.uuid4().hex[:8]}",
            problem_id=problem_id,
            ordinal=data.ordinal,
            stdin=data.stdin,
            expected_stdout=data.expected_stdout,
            checker=data.checker,
            checker_args=data.checker_args,
            is_sample=data.is_sample,
            weight=data.weight,
            time_limit_s=data.time_limit_s,
            memory_kb=data.memory_kb,
        )
        await self._testcase_repo.create(case)
        return self._to_admin_case(case)

    # ── mapping ────────────────────────────────────────────────────

    @staticmethod
    def _to_summary(p: Problem) -> ProblemSummary:
        return ProblemSummary(
            id=p.id, slug=p.slug, title=p.title, difficulty=p.difficulty, tags=p.tags
        )

    @staticmethod
    def _to_detail(p: Problem, samples: list[TestCaseSample]) -> ProblemDetail:
        return ProblemDetail(
            id=p.id,
            slug=p.slug,
            title=p.title,
            difficulty=p.difficulty,
            tags=p.tags,
            statement_md=p.statement_md,
            starter_code=p.starter_code,
            judge_mode=p.judge_mode,
            time_limit_s=p.time_limit_s,
            memory_kb=p.memory_kb,
            sample_testcases=samples,
            harness_files=dict(p.harness.get("files") or {}) if p.harness else None,
        )

    @staticmethod
    def _to_admin_case(c: TestCase) -> TestCaseAdmin:
        return TestCaseAdmin(
            id=c.id,
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

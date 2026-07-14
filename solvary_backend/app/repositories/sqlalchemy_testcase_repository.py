from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import TestCaseRow
from app.models.testcase import TestCase
from app.repositories.testcase_repository import TestCaseRepository


class SQLAlchemyTestCaseRepository(TestCaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> TestCase | None:
        row = await self._session.get(TestCaseRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_by_problem(self, problem_id: str) -> list[TestCase]:
        stmt = (
            select(TestCaseRow)
            .where(TestCaseRow.problem_id == problem_id)
            .order_by(TestCaseRow.ordinal.asc())
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_all(self, **filters: object) -> list[TestCase]:
        stmt = select(TestCaseRow).order_by(TestCaseRow.problem_id, TestCaseRow.ordinal)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: TestCase) -> TestCase:
        row = TestCaseRow(
            id=entity.id,
            problem_id=entity.problem_id,
            ordinal=entity.ordinal,
            stdin=entity.stdin,
            expected_stdout=entity.expected_stdout,
            checker=entity.checker,
            checker_args=entity.checker_args,
            is_sample=entity.is_sample,
            weight=entity.weight,
            time_limit_s=entity.time_limit_s,
            memory_kb=entity.memory_kb,
        )
        self._session.add(row)
        await self._session.flush()
        return entity

    async def update(self, entity: TestCase) -> TestCase:
        row = await self._session.get(TestCaseRow, entity.id)
        if row:
            row.ordinal = entity.ordinal
            row.stdin = entity.stdin
            row.expected_stdout = entity.expected_stdout
            row.checker = entity.checker
            row.checker_args = entity.checker_args
            row.is_sample = entity.is_sample
            row.weight = entity.weight
            row.time_limit_s = entity.time_limit_s
            row.memory_kb = entity.memory_kb
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        stmt = sa_delete(TestCaseRow).where(TestCaseRow.id == entity_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: TestCaseRow) -> TestCase:
        return TestCase(
            id=row.id,
            problem_id=row.problem_id,
            ordinal=row.ordinal,
            stdin=row.stdin,
            expected_stdout=row.expected_stdout,
            checker=row.checker,  # type: ignore[arg-type]
            checker_args=dict(row.checker_args or {}),
            is_sample=row.is_sample,
            weight=row.weight,
            time_limit_s=row.time_limit_s,
            memory_kb=row.memory_kb,
        )

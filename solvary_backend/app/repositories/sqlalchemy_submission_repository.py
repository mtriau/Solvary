from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import SubmissionRow
from app.models.submission import Submission
from app.repositories.submission_repository import SubmissionRepository


class SQLAlchemySubmissionRepository(SubmissionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> Submission | None:
        row = await self._session.get(SubmissionRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_paginated(
        self,
        user_id: str | None = None,
        problem_id: str | None = None,
        workspace_id: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Submission], str | None]:
        stmt = select(SubmissionRow)
        if user_id:
            stmt = stmt.where(SubmissionRow.user_id == user_id)
        if problem_id:
            stmt = stmt.where(SubmissionRow.problem_id == problem_id)
        if workspace_id:
            stmt = stmt.where(SubmissionRow.workspace_id == workspace_id)

        # Newest first; tie-safe keyset on (created_at, id) descending —
        # submissions burst-insert, so timestamp ties are the norm here
        # (see SOLVARY_DESIGN.md §3.3).
        stmt = stmt.order_by(SubmissionRow.created_at.desc(), SubmissionRow.id.desc())
        if cursor:
            cursor_row = await self._session.get(SubmissionRow, cursor)
            if cursor_row:
                stmt = stmt.where(
                    or_(
                        SubmissionRow.created_at < cursor_row.created_at,
                        and_(
                            SubmissionRow.created_at == cursor_row.created_at,
                            SubmissionRow.id < cursor_row.id,
                        ),
                    )
                )

        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        has_next = len(rows) > limit
        page = rows[:limit]
        next_cursor = page[-1].id if has_next and page else None
        return [self._to_domain(r) for r in page], next_cursor

    async def list_by_user(self, user_id: str) -> list[Submission]:
        stmt = select(SubmissionRow).where(SubmissionRow.user_id == user_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def find_stale(self, cutoff: datetime) -> list[Submission]:
        stmt = select(SubmissionRow).where(
            SubmissionRow.verdict.in_(("queued", "running")),
            SubmissionRow.updated_at < cutoff,
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_all(self, **filters: object) -> list[Submission]:
        stmt = select(SubmissionRow).order_by(SubmissionRow.created_at)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: Submission) -> Submission:
        row = SubmissionRow(
            id=entity.id,
            user_id=entity.user_id,
            problem_id=entity.problem_id,
            workspace_id=entity.workspace_id,
            language=entity.language,
            code=entity.code,
            verdict=entity.verdict,
            runtime_ms=entity.runtime_ms,
            memory_kb=entity.memory_kb,
            passed=entity.passed,
            total=entity.total,
            test_results=entity.test_results,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return entity

    async def update(self, entity: Submission) -> Submission:
        row = await self._session.get(SubmissionRow, entity.id)
        if row:
            row.verdict = entity.verdict
            row.runtime_ms = entity.runtime_ms
            row.memory_kb = entity.memory_kb
            row.passed = entity.passed
            row.total = entity.total
            row.test_results = entity.test_results
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        stmt = sa_delete(SubmissionRow).where(SubmissionRow.id == entity_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: SubmissionRow) -> Submission:
        return Submission(
            id=row.id,
            user_id=row.user_id,
            problem_id=row.problem_id,
            workspace_id=row.workspace_id,
            language=row.language,
            code=row.code,
            verdict=row.verdict,  # type: ignore[arg-type]
            runtime_ms=row.runtime_ms,
            memory_kb=row.memory_kb,
            passed=row.passed,
            total=row.total,
            test_results=list(row.test_results or []),
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import ProblemRow
from app.models.problem import Problem
from app.repositories.problem_repository import ProblemRepository


class SQLAlchemyProblemRepository(ProblemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> Problem | None:
        row = await self._session.get(ProblemRow, entity_id)
        return self._to_domain(row) if row else None

    async def get_by_slug(self, slug: str) -> Problem | None:
        stmt = select(ProblemRow).where(ProblemRow.slug == slug)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_paginated(
        self,
        difficulty: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Problem], str | None]:
        stmt = select(ProblemRow).where(ProblemRow.is_public.is_(True))
        if difficulty:
            stmt = stmt.where(ProblemRow.difficulty == difficulty)
        if q:
            stmt = stmt.where(ProblemRow.title.ilike(f"%{q}%"))

        # Tie-safe keyset pagination on (created_at, id) — deliberate deviation
        # from MattChat's strictly-greater created_at cursor, which skips
        # rows sharing the cursor's timestamp (see SOLVARY_DESIGN.md §3.3).
        stmt = stmt.order_by(ProblemRow.created_at.asc(), ProblemRow.id.asc())
        if cursor:
            cursor_row = await self._session.get(ProblemRow, cursor)
            if cursor_row:
                stmt = stmt.where(
                    or_(
                        ProblemRow.created_at > cursor_row.created_at,
                        and_(
                            ProblemRow.created_at == cursor_row.created_at,
                            ProblemRow.id > cursor_row.id,
                        ),
                    )
                )

        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())

        # Tag filter applied post-query (JSON list column; fine at MVP scale)
        domains = [self._to_domain(r) for r in rows]
        if tag:
            domains = [p for p in domains if tag in p.tags]

        has_next = len(rows) > limit
        page = domains[:limit]
        next_cursor = page[-1].id if has_next and page else None
        return page, next_cursor

    async def list_all(self, **filters: object) -> list[Problem]:
        stmt = select(ProblemRow).order_by(ProblemRow.created_at)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: Problem) -> Problem:
        row = ProblemRow(
            id=entity.id,
            slug=entity.slug,
            title=entity.title,
            difficulty=entity.difficulty,
            statement_md=entity.statement_md,
            tags=entity.tags,
            starter_code=entity.starter_code,
            function_signature=entity.function_signature,
            judge_mode=entity.judge_mode,
            harness=entity.harness,
            time_limit_s=entity.time_limit_s,
            memory_kb=entity.memory_kb,
            editorial_md=entity.editorial_md,
            is_public=entity.is_public,
            created_by=entity.created_by,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return entity

    async def update(self, entity: Problem) -> Problem:
        row = await self._session.get(ProblemRow, entity.id)
        if row:
            row.title = entity.title
            row.difficulty = entity.difficulty
            row.statement_md = entity.statement_md
            row.tags = entity.tags
            row.starter_code = entity.starter_code
            row.function_signature = entity.function_signature
            row.judge_mode = entity.judge_mode
            row.harness = entity.harness
            row.time_limit_s = entity.time_limit_s
            row.memory_kb = entity.memory_kb
            row.editorial_md = entity.editorial_md
            row.is_public = entity.is_public
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        stmt = sa_delete(ProblemRow).where(ProblemRow.id == entity_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: ProblemRow) -> Problem:
        return Problem(
            id=row.id,
            slug=row.slug,
            title=row.title,
            difficulty=row.difficulty,  # type: ignore[arg-type]
            statement_md=row.statement_md,
            tags=list(row.tags or []),
            starter_code=dict(row.starter_code or {}),
            function_signature=row.function_signature,
            judge_mode=row.judge_mode,  # type: ignore[arg-type]
            harness=dict(row.harness) if row.harness else None,
            time_limit_s=row.time_limit_s,
            memory_kb=row.memory_kb,
            editorial_md=row.editorial_md,
            is_public=row.is_public,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

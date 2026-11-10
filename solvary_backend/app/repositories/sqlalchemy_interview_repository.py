from datetime import UTC, datetime

from sqlalchemy import and_, or_, select
from sqlalchemy import delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import InterviewSessionRow, InterviewStageRow, InterviewTemplateRow
from app.models.interview import InterviewSession, InterviewStage, InterviewTemplate
from app.repositories.interview_repository import (
    InterviewSessionRepository,
    InterviewStageRepository,
    InterviewTemplateRepository,
)


class SQLAlchemyInterviewTemplateRepository(InterviewTemplateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> InterviewTemplate | None:
        row = await self._session.get(InterviewTemplateRow, entity_id)
        return self._to_domain(row) if row else None

    async def get_by_slug(self, slug: str) -> InterviewTemplate | None:
        stmt = select(InterviewTemplateRow).where(InterviewTemplateRow.slug == slug)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_public(self) -> list[InterviewTemplate]:
        stmt = (
            select(InterviewTemplateRow)
            .where(InterviewTemplateRow.is_public.is_(True))
            .order_by(InterviewTemplateRow.created_at, InterviewTemplateRow.id)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_all(self, **filters: object) -> list[InterviewTemplate]:
        stmt = select(InterviewTemplateRow).order_by(InterviewTemplateRow.created_at)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: InterviewTemplate) -> InterviewTemplate:
        self._session.add(
            InterviewTemplateRow(
                id=entity.id,
                slug=entity.slug,
                title=entity.title,
                description_md=entity.description_md,
                format=entity.format,
                duration_s=entity.duration_s,
                advance=entity.advance,
                pacing=entity.pacing,
                is_public=entity.is_public,
                created_by=entity.created_by,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: InterviewTemplate) -> InterviewTemplate:
        row = await self._session.get(InterviewTemplateRow, entity.id)
        if row:
            row.title = entity.title
            row.description_md = entity.description_md
            row.format = entity.format
            row.duration_s = entity.duration_s
            row.advance = entity.advance
            row.pacing = entity.pacing
            row.is_public = entity.is_public
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(InterviewTemplateRow).where(InterviewTemplateRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: InterviewTemplateRow) -> InterviewTemplate:
        return InterviewTemplate(
            id=row.id,
            slug=row.slug,
            title=row.title,
            description_md=row.description_md,
            format=row.format,  # type: ignore[arg-type]
            duration_s=row.duration_s,
            advance=row.advance,  # type: ignore[arg-type]
            pacing=row.pacing,  # type: ignore[arg-type]
            is_public=row.is_public,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SQLAlchemyInterviewStageRepository(InterviewStageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> InterviewStage | None:
        row = await self._session.get(InterviewStageRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_by_template(self, template_id: str) -> list[InterviewStage]:
        stmt = (
            select(InterviewStageRow)
            .where(InterviewStageRow.template_id == template_id)
            .order_by(InterviewStageRow.ordinal)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_problem(self, problem_id: str) -> list[InterviewStage]:
        stmt = select(InterviewStageRow).where(InterviewStageRow.problem_id == problem_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_all(self, **filters: object) -> list[InterviewStage]:
        result = await self._session.execute(select(InterviewStageRow))
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: InterviewStage) -> InterviewStage:
        self._session.add(
            InterviewStageRow(
                id=entity.id,
                template_id=entity.template_id,
                ordinal=entity.ordinal,
                problem_id=entity.problem_id,
                title=entity.title,
                budget_s=entity.budget_s,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: InterviewStage) -> InterviewStage:
        row = await self._session.get(InterviewStageRow, entity.id)
        if row:
            row.ordinal = entity.ordinal
            row.problem_id = entity.problem_id
            row.title = entity.title
            row.budget_s = entity.budget_s
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(InterviewStageRow).where(InterviewStageRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: InterviewStageRow) -> InterviewStage:
        return InterviewStage(
            id=row.id,
            template_id=row.template_id,
            ordinal=row.ordinal,
            problem_id=row.problem_id,
            title=row.title,
            budget_s=row.budget_s,
        )


class SQLAlchemyInterviewSessionRepository(InterviewSessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> InterviewSession | None:
        row = await self._session.get(InterviewSessionRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_paginated(
        self, user_id: str, cursor: str | None = None, limit: int = 50
    ) -> tuple[list[InterviewSession], str | None]:
        stmt = (
            select(InterviewSessionRow)
            .where(InterviewSessionRow.user_id == user_id)
            .order_by(InterviewSessionRow.created_at.desc(), InterviewSessionRow.id.desc())
        )
        if cursor:
            cursor_row = await self._session.get(InterviewSessionRow, cursor)
            if cursor_row:
                stmt = stmt.where(
                    or_(
                        InterviewSessionRow.created_at < cursor_row.created_at,
                        and_(
                            InterviewSessionRow.created_at == cursor_row.created_at,
                            InterviewSessionRow.id < cursor_row.id,
                        ),
                    )
                )
        stmt = stmt.limit(limit + 1)
        rows = list((await self._session.execute(stmt)).scalars().all())
        has_next = len(rows) > limit
        page = rows[:limit]
        next_cursor = page[-1].id if has_next and page else None
        return [self._to_domain(r) for r in page], next_cursor

    async def get_active_for_user(self, user_id: str) -> InterviewSession | None:
        stmt = (
            select(InterviewSessionRow)
            .where(
                InterviewSessionRow.user_id == user_id,
                InterviewSessionRow.status == "active",
            )
            .order_by(InterviewSessionRow.created_at.desc())
            .limit(1)
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_by_user(self, user_id: str) -> list[InterviewSession]:
        stmt = select(InterviewSessionRow).where(InterviewSessionRow.user_id == user_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_all(self, **filters: object) -> list[InterviewSession]:
        result = await self._session.execute(select(InterviewSessionRow))
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: InterviewSession) -> InterviewSession:
        self._session.add(
            InterviewSessionRow(
                id=entity.id,
                template_id=entity.template_id,
                user_id=entity.user_id,
                language=entity.language,
                workspace_id=entity.workspace_id,
                status=entity.status,
                started_at=entity.started_at,
                ends_at=entity.ends_at,
                finished_at=entity.finished_at,
                current_stage=entity.current_stage,
                unlocked_through=entity.unlocked_through,
                stage_files=dict(entity.stage_files),
                timeline=list(entity.timeline),
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: InterviewSession) -> InterviewSession:
        row = await self._session.get(InterviewSessionRow, entity.id)
        if row:
            row.status = entity.status
            row.finished_at = entity.finished_at
            row.current_stage = entity.current_stage
            row.unlocked_through = entity.unlocked_through
            row.stage_files = dict(entity.stage_files)
            row.timeline = list(entity.timeline)  # new list → JSON change detected
            row.workspace_id = entity.workspace_id
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(InterviewSessionRow).where(InterviewSessionRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _aware(dt: datetime | None) -> datetime | None:
        # SQLite returns naive datetimes; the clock math needs tz-aware UTC
        if dt is not None and dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)
        return dt

    @classmethod
    def _to_domain(cls, row: InterviewSessionRow) -> InterviewSession:
        return InterviewSession(
            id=row.id,
            template_id=row.template_id,
            user_id=row.user_id,
            language=row.language,
            workspace_id=row.workspace_id,
            status=row.status,  # type: ignore[arg-type]
            started_at=cls._aware(row.started_at),  # type: ignore[arg-type]
            ends_at=cls._aware(row.ends_at),  # type: ignore[arg-type]
            finished_at=cls._aware(row.finished_at),
            current_stage=row.current_stage,
            unlocked_through=row.unlocked_through,
            stage_files=dict(row.stage_files or {}),
            timeline=list(row.timeline or []),
            created_at=cls._aware(row.created_at),  # type: ignore[arg-type]
            updated_at=cls._aware(row.updated_at),  # type: ignore[arg-type]
        )

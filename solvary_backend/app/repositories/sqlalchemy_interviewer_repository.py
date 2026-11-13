from datetime import UTC, datetime

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import InterviewerTurnRow
from app.models.interviewer import InterviewerTurn
from app.repositories.interviewer_repository import InterviewerTurnRepository


class SQLAlchemyInterviewerTurnRepository(InterviewerTurnRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> InterviewerTurn | None:
        row = await self._session.get(InterviewerTurnRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_by_session(self, session_id: str) -> list[InterviewerTurn]:
        stmt = (
            select(InterviewerTurnRow)
            .where(InterviewerTurnRow.session_id == session_id)
            .order_by(InterviewerTurnRow.ordinal)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def next_ordinal(self, session_id: str) -> int:
        stmt = select(func.max(InterviewerTurnRow.ordinal)).where(
            InterviewerTurnRow.session_id == session_id
        )
        current = (await self._session.execute(stmt)).scalar_one_or_none()
        return (current or 0) + 1

    async def delete_by_session(self, session_id: str) -> int:
        result = await self._session.execute(
            sa_delete(InterviewerTurnRow).where(InterviewerTurnRow.session_id == session_id)
        )
        return result.rowcount or 0

    async def list_all(self, **filters: object) -> list[InterviewerTurn]:
        result = await self._session.execute(
            select(InterviewerTurnRow).order_by(InterviewerTurnRow.created_at)
        )
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: InterviewerTurn) -> InterviewerTurn:
        self._session.add(
            InterviewerTurnRow(
                id=entity.id,
                session_id=entity.session_id,
                user_id=entity.user_id,
                ordinal=entity.ordinal,
                role=entity.role,
                trigger=entity.trigger,
                content=entity.content,
                digest=entity.digest,
                silent=entity.silent,
                model=entity.model,
                input_tokens=entity.input_tokens,
                output_tokens=entity.output_tokens,
                cache_read_input_tokens=entity.cache_read_input_tokens,
                cache_creation_input_tokens=entity.cache_creation_input_tokens,
                created_at=entity.created_at,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: InterviewerTurn) -> InterviewerTurn:
        row = await self._session.get(InterviewerTurnRow, entity.id)
        if row:
            row.content = entity.content
            row.digest = entity.digest
            row.silent = entity.silent
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(InterviewerTurnRow).where(InterviewerTurnRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: InterviewerTurnRow) -> InterviewerTurn:
        created = row.created_at
        if created is not None and created.tzinfo is None:
            created = created.replace(tzinfo=UTC)  # SQLite hands back naive datetimes
        return InterviewerTurn(
            id=row.id,
            session_id=row.session_id,
            user_id=row.user_id,
            ordinal=row.ordinal,
            role=row.role,  # type: ignore[arg-type]
            trigger=row.trigger,  # type: ignore[arg-type]
            content=row.content,
            digest=row.digest or "",
            silent=bool(row.silent),
            model=row.model,
            input_tokens=row.input_tokens,
            output_tokens=row.output_tokens,
            cache_read_input_tokens=row.cache_read_input_tokens,
            cache_creation_input_tokens=row.cache_creation_input_tokens,
            created_at=created or datetime.now(UTC),
        )

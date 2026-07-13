from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import DocSnapshotRow, DocUpdateRow
from app.models.doc import DocSnapshot, DocUpdate
from app.repositories.doc_repository import DocRepository


class SQLAlchemyDocRepository(DocRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def latest_snapshot(self, workspace_id: str) -> DocSnapshot | None:
        stmt = (
            select(DocSnapshotRow)
            .where(DocSnapshotRow.workspace_id == workspace_id)
            .order_by(DocSnapshotRow.update_seq.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return DocSnapshot(
            id=row.id,
            workspace_id=row.workspace_id,
            state=row.state,
            update_seq=row.update_seq,
            created_at=row.created_at,
        )

    async def save_snapshot(self, snapshot: DocSnapshot) -> DocSnapshot:
        self._session.add(
            DocSnapshotRow(
                id=snapshot.id,
                workspace_id=snapshot.workspace_id,
                state=snapshot.state,
                update_seq=snapshot.update_seq,
                created_at=snapshot.created_at,
            )
        )
        # Only the latest snapshot matters; drop superseded ones
        await self._session.execute(
            sa_delete(DocSnapshotRow).where(
                DocSnapshotRow.workspace_id == snapshot.workspace_id,
                DocSnapshotRow.update_seq < snapshot.update_seq,
            )
        )
        await self._session.flush()
        return snapshot

    async def updates_after(self, workspace_id: str, seq: int) -> list[DocUpdate]:
        stmt = (
            select(DocUpdateRow)
            .where(DocUpdateRow.workspace_id == workspace_id, DocUpdateRow.seq > seq)
            .order_by(DocUpdateRow.seq.asc())
        )
        result = await self._session.execute(stmt)
        return [
            DocUpdate(
                id=r.id,
                workspace_id=r.workspace_id,
                seq=r.seq,
                payload=r.payload,
                created_at=r.created_at,
            )
            for r in result.scalars().all()
        ]

    async def append_update(self, update: DocUpdate) -> DocUpdate:
        self._session.add(
            DocUpdateRow(
                id=update.id,
                workspace_id=update.workspace_id,
                seq=update.seq,
                payload=update.payload,
                created_at=update.created_at,
            )
        )
        await self._session.flush()
        return update

    async def delete_updates_upto(self, workspace_id: str, seq: int) -> int:
        result = await self._session.execute(
            sa_delete(DocUpdateRow).where(
                DocUpdateRow.workspace_id == workspace_id, DocUpdateRow.seq <= seq
            )
        )
        return result.rowcount or 0

    async def max_seq(self, workspace_id: str) -> int:
        stmt = select(func.max(DocUpdateRow.seq)).where(
            DocUpdateRow.workspace_id == workspace_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() or 0

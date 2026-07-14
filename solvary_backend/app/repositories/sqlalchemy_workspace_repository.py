from datetime import UTC, datetime

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import WorkspaceFileRow, WorkspaceMemberRow, WorkspaceRow
from app.models.workspace import Workspace, WorkspaceFile, WorkspaceMember
from app.repositories.workspace_repository import (
    FileRepository,
    MemberRepository,
    WorkspaceRepository,
)


class SQLAlchemyWorkspaceRepository(WorkspaceRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> Workspace | None:
        row = await self._session.get(WorkspaceRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_all(self, **filters: object) -> list[Workspace]:
        stmt = select(WorkspaceRow).order_by(WorkspaceRow.created_at)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: Workspace) -> Workspace:
        self._session.add(
            WorkspaceRow(
                id=entity.id,
                name=entity.name,
                owner_id=entity.owner_id,
                language=entity.language,
                problem_id=entity.problem_id,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: Workspace) -> Workspace:
        row = await self._session.get(WorkspaceRow, entity.id)
        if row:
            row.name = entity.name
            row.language = entity.language
            row.problem_id = entity.problem_id
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(WorkspaceRow).where(WorkspaceRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: WorkspaceRow) -> Workspace:
        return Workspace(
            id=row.id,
            name=row.name,
            owner_id=row.owner_id,
            language=row.language,
            problem_id=row.problem_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class SQLAlchemyMemberRepository(MemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> WorkspaceMember | None:
        row = await self._session.get(WorkspaceMemberRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_by_workspace(self, workspace_id: str) -> list[WorkspaceMember]:
        stmt = select(WorkspaceMemberRow).where(
            WorkspaceMemberRow.workspace_id == workspace_id
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def list_by_user(self, user_id: str) -> list[WorkspaceMember]:
        stmt = select(WorkspaceMemberRow).where(WorkspaceMemberRow.user_id == user_id)
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_by_workspace_and_user(
        self, workspace_id: str, user_id: str
    ) -> WorkspaceMember | None:
        stmt = select(WorkspaceMemberRow).where(
            WorkspaceMemberRow.workspace_id == workspace_id,
            WorkspaceMemberRow.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_all(self, **filters: object) -> list[WorkspaceMember]:
        result = await self._session.execute(select(WorkspaceMemberRow))
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: WorkspaceMember) -> WorkspaceMember:
        self._session.add(
            WorkspaceMemberRow(
                id=entity.id,
                workspace_id=entity.workspace_id,
                user_id=entity.user_id,
                role=entity.role,
                created_at=entity.created_at,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: WorkspaceMember) -> WorkspaceMember:
        row = await self._session.get(WorkspaceMemberRow, entity.id)
        if row:
            row.role = entity.role
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(WorkspaceMemberRow).where(WorkspaceMemberRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: WorkspaceMemberRow) -> WorkspaceMember:
        return WorkspaceMember(
            id=row.id,
            workspace_id=row.workspace_id,
            user_id=row.user_id,
            role=row.role,  # type: ignore[arg-type]
            created_at=row.created_at,
        )


class SQLAlchemyFileRepository(FileRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> WorkspaceFile | None:
        row = await self._session.get(WorkspaceFileRow, entity_id)
        return self._to_domain(row) if row else None

    async def list_by_workspace(self, workspace_id: str) -> list[WorkspaceFile]:
        stmt = (
            select(WorkspaceFileRow)
            .where(WorkspaceFileRow.workspace_id == workspace_id)
            .order_by(WorkspaceFileRow.path)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(r) for r in result.scalars().all()]

    async def get_by_workspace_and_path(
        self, workspace_id: str, path: str
    ) -> WorkspaceFile | None:
        stmt = select(WorkspaceFileRow).where(
            WorkspaceFileRow.workspace_id == workspace_id,
            WorkspaceFileRow.path == path,
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_all(self, **filters: object) -> list[WorkspaceFile]:
        result = await self._session.execute(select(WorkspaceFileRow))
        return [self._to_domain(r) for r in result.scalars().all()]

    async def create(self, entity: WorkspaceFile) -> WorkspaceFile:
        self._session.add(
            WorkspaceFileRow(
                id=entity.id,
                workspace_id=entity.workspace_id,
                path=entity.path,
                language=entity.language,
                created_at=entity.created_at,
                updated_at=entity.updated_at,
            )
        )
        await self._session.flush()
        return entity

    async def update(self, entity: WorkspaceFile) -> WorkspaceFile:
        row = await self._session.get(WorkspaceFileRow, entity.id)
        if row:
            row.path = entity.path
            row.language = entity.language
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        result = await self._session.execute(
            sa_delete(WorkspaceFileRow).where(WorkspaceFileRow.id == entity_id)
        )
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: WorkspaceFileRow) -> WorkspaceFile:
        return WorkspaceFile(
            id=row.id,
            workspace_id=row.workspace_id,
            path=row.path,
            language=row.language,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

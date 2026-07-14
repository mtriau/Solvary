from abc import abstractmethod

from app.models.workspace import Workspace, WorkspaceFile, WorkspaceMember
from app.repositories.base import AbstractRepository


class WorkspaceRepository(AbstractRepository[Workspace]):
    pass


class MemberRepository(AbstractRepository[WorkspaceMember]):
    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[WorkspaceMember]: ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[WorkspaceMember]: ...

    @abstractmethod
    async def get_by_workspace_and_user(
        self, workspace_id: str, user_id: str
    ) -> WorkspaceMember | None: ...


class FileRepository(AbstractRepository[WorkspaceFile]):
    @abstractmethod
    async def list_by_workspace(self, workspace_id: str) -> list[WorkspaceFile]: ...

    @abstractmethod
    async def get_by_workspace_and_path(
        self, workspace_id: str, path: str
    ) -> WorkspaceFile | None: ...


# ── Mocks ──────────────────────────────────────────────────────────


class MockWorkspaceRepository(WorkspaceRepository):
    def __init__(self) -> None:
        self._items: list[Workspace] = []

    async def get_by_id(self, entity_id: str) -> Workspace | None:
        return next((w for w in self._items if w.id == entity_id), None)

    async def list_all(self, **filters: object) -> list[Workspace]:
        return list(self._items)

    async def create(self, entity: Workspace) -> Workspace:
        self._items.append(entity)
        return entity

    async def update(self, entity: Workspace) -> Workspace:
        for i, w in enumerate(self._items):
            if w.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [w for w in self._items if w.id != entity_id]
        return len(self._items) < before


class MockMemberRepository(MemberRepository):
    def __init__(self) -> None:
        self._items: list[WorkspaceMember] = []

    async def get_by_id(self, entity_id: str) -> WorkspaceMember | None:
        return next((m for m in self._items if m.id == entity_id), None)

    async def list_by_workspace(self, workspace_id: str) -> list[WorkspaceMember]:
        return [m for m in self._items if m.workspace_id == workspace_id]

    async def list_by_user(self, user_id: str) -> list[WorkspaceMember]:
        return [m for m in self._items if m.user_id == user_id]

    async def get_by_workspace_and_user(
        self, workspace_id: str, user_id: str
    ) -> WorkspaceMember | None:
        return next(
            (
                m
                for m in self._items
                if m.workspace_id == workspace_id and m.user_id == user_id
            ),
            None,
        )

    async def list_all(self, **filters: object) -> list[WorkspaceMember]:
        return list(self._items)

    async def create(self, entity: WorkspaceMember) -> WorkspaceMember:
        self._items.append(entity)
        return entity

    async def update(self, entity: WorkspaceMember) -> WorkspaceMember:
        for i, m in enumerate(self._items):
            if m.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [m for m in self._items if m.id != entity_id]
        return len(self._items) < before


class MockFileRepository(FileRepository):
    def __init__(self) -> None:
        self._items: list[WorkspaceFile] = []

    async def get_by_id(self, entity_id: str) -> WorkspaceFile | None:
        return next((f for f in self._items if f.id == entity_id), None)

    async def list_by_workspace(self, workspace_id: str) -> list[WorkspaceFile]:
        return sorted(
            (f for f in self._items if f.workspace_id == workspace_id),
            key=lambda f: f.path,
        )

    async def get_by_workspace_and_path(
        self, workspace_id: str, path: str
    ) -> WorkspaceFile | None:
        return next(
            (
                f
                for f in self._items
                if f.workspace_id == workspace_id and f.path == path
            ),
            None,
        )

    async def list_all(self, **filters: object) -> list[WorkspaceFile]:
        return list(self._items)

    async def create(self, entity: WorkspaceFile) -> WorkspaceFile:
        self._items.append(entity)
        return entity

    async def update(self, entity: WorkspaceFile) -> WorkspaceFile:
        for i, f in enumerate(self._items):
            if f.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [f for f in self._items if f.id != entity_id]
        return len(self._items) < before

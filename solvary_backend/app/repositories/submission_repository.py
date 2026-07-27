from abc import abstractmethod
from datetime import datetime

from app.models.submission import Submission
from app.repositories.base import AbstractRepository


class SubmissionRepository(AbstractRepository[Submission]):
    @abstractmethod
    async def list_paginated(
        self,
        user_id: str | None = None,
        problem_id: str | None = None,
        workspace_id: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Submission], str | None]:
        """Newest first."""
        ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[Submission]:
        """Every submission by a user — stats computation."""
        ...

    @abstractmethod
    async def find_stale(self, cutoff: datetime) -> list[Submission]:
        """Non-terminal submissions not updated since cutoff — the worker
        persists incrementally, so live jobs always have fresh updated_at."""
        ...


class MockSubmissionRepository(SubmissionRepository):
    def __init__(self) -> None:
        self._submissions: list[Submission] = []

    async def get_by_id(self, entity_id: str) -> Submission | None:
        return next((s for s in self._submissions if s.id == entity_id), None)

    async def list_paginated(
        self,
        user_id: str | None = None,
        problem_id: str | None = None,
        workspace_id: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Submission], str | None]:
        items = list(self._submissions)
        if user_id:
            items = [s for s in items if s.user_id == user_id]
        if problem_id:
            items = [s for s in items if s.problem_id == problem_id]
        if workspace_id:
            items = [s for s in items if s.workspace_id == workspace_id]
        items.sort(key=lambda s: (s.created_at, s.id), reverse=True)

        if cursor:
            start = next((i + 1 for i, s in enumerate(items) if s.id == cursor), 0)
            items = items[start:]

        page = items[:limit]
        next_cursor = page[-1].id if len(items) > limit and page else None
        return page, next_cursor

    async def list_by_user(self, user_id: str) -> list[Submission]:
        return [s for s in self._submissions if s.user_id == user_id]

    async def find_stale(self, cutoff: datetime) -> list[Submission]:
        return [
            s
            for s in self._submissions
            if s.verdict in ("queued", "running") and s.updated_at < cutoff
        ]

    async def list_all(self, **filters: object) -> list[Submission]:
        return list(self._submissions)

    async def create(self, entity: Submission) -> Submission:
        self._submissions.append(entity)
        return entity

    async def update(self, entity: Submission) -> Submission:
        for i, s in enumerate(self._submissions):
            if s.id == entity.id:
                self._submissions[i] = entity
                return entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._submissions)
        self._submissions = [s for s in self._submissions if s.id != entity_id]
        return len(self._submissions) < before

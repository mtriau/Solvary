from abc import abstractmethod

from app.models.interview import InterviewSession, InterviewStage, InterviewTemplate
from app.repositories.base import AbstractRepository


class InterviewTemplateRepository(AbstractRepository[InterviewTemplate]):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> InterviewTemplate | None: ...

    @abstractmethod
    async def list_public(self) -> list[InterviewTemplate]:
        """Oldest first (catalog order)."""
        ...


class InterviewStageRepository(AbstractRepository[InterviewStage]):
    @abstractmethod
    async def list_by_template(self, template_id: str) -> list[InterviewStage]:
        """Ordered by ordinal."""
        ...

    @abstractmethod
    async def list_by_problem(self, problem_id: str) -> list[InterviewStage]: ...


class InterviewSessionRepository(AbstractRepository[InterviewSession]):
    @abstractmethod
    async def list_paginated(
        self, user_id: str, cursor: str | None = None, limit: int = 50
    ) -> tuple[list[InterviewSession], str | None]:
        """Newest first, tie-safe keyset on (created_at, id)."""
        ...

    @abstractmethod
    async def get_active_for_user(self, user_id: str) -> InterviewSession | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: str) -> list[InterviewSession]: ...


# ── Mocks ──────────────────────────────────────────────────────────


class MockInterviewTemplateRepository(InterviewTemplateRepository):
    def __init__(self) -> None:
        self._items: list[InterviewTemplate] = []

    async def get_by_id(self, entity_id: str) -> InterviewTemplate | None:
        return next((t for t in self._items if t.id == entity_id), None)

    async def get_by_slug(self, slug: str) -> InterviewTemplate | None:
        return next((t for t in self._items if t.slug == slug), None)

    async def list_public(self) -> list[InterviewTemplate]:
        return sorted(
            (t for t in self._items if t.is_public), key=lambda t: (t.created_at, t.id)
        )

    async def list_all(self, **filters: object) -> list[InterviewTemplate]:
        return list(self._items)

    async def create(self, entity: InterviewTemplate) -> InterviewTemplate:
        self._items.append(entity)
        return entity

    async def update(self, entity: InterviewTemplate) -> InterviewTemplate:
        for i, t in enumerate(self._items):
            if t.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [t for t in self._items if t.id != entity_id]
        return len(self._items) < before


class MockInterviewStageRepository(InterviewStageRepository):
    def __init__(self) -> None:
        self._items: list[InterviewStage] = []

    async def get_by_id(self, entity_id: str) -> InterviewStage | None:
        return next((s for s in self._items if s.id == entity_id), None)

    async def list_by_template(self, template_id: str) -> list[InterviewStage]:
        return sorted(
            (s for s in self._items if s.template_id == template_id), key=lambda s: s.ordinal
        )

    async def list_by_problem(self, problem_id: str) -> list[InterviewStage]:
        return [s for s in self._items if s.problem_id == problem_id]

    async def list_all(self, **filters: object) -> list[InterviewStage]:
        return list(self._items)

    async def create(self, entity: InterviewStage) -> InterviewStage:
        self._items.append(entity)
        return entity

    async def update(self, entity: InterviewStage) -> InterviewStage:
        for i, s in enumerate(self._items):
            if s.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [s for s in self._items if s.id != entity_id]
        return len(self._items) < before


class MockInterviewSessionRepository(InterviewSessionRepository):
    def __init__(self) -> None:
        self._items: list[InterviewSession] = []

    async def get_by_id(self, entity_id: str) -> InterviewSession | None:
        return next((s for s in self._items if s.id == entity_id), None)

    async def list_paginated(
        self, user_id: str, cursor: str | None = None, limit: int = 50
    ) -> tuple[list[InterviewSession], str | None]:
        items = [s for s in self._items if s.user_id == user_id]
        items.sort(key=lambda s: (s.created_at, s.id), reverse=True)
        if cursor:
            start = next((i + 1 for i, s in enumerate(items) if s.id == cursor), 0)
            items = items[start:]
        page = items[:limit]
        next_cursor = page[-1].id if len(items) > limit and page else None
        return page, next_cursor

    async def get_active_for_user(self, user_id: str) -> InterviewSession | None:
        return next(
            (s for s in self._items if s.user_id == user_id and s.status == "active"), None
        )

    async def list_by_user(self, user_id: str) -> list[InterviewSession]:
        return [s for s in self._items if s.user_id == user_id]

    async def list_all(self, **filters: object) -> list[InterviewSession]:
        return list(self._items)

    async def create(self, entity: InterviewSession) -> InterviewSession:
        self._items.append(entity)
        return entity

    async def update(self, entity: InterviewSession) -> InterviewSession:
        for i, s in enumerate(self._items):
            if s.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [s for s in self._items if s.id != entity_id]
        return len(self._items) < before

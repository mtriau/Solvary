from abc import abstractmethod

from app.mock_data.problems import MOCK_PROBLEMS
from app.models.problem import Problem
from app.repositories.base import AbstractRepository


class ProblemRepository(AbstractRepository[Problem]):
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Problem | None: ...

    @abstractmethod
    async def list_paginated(
        self,
        difficulty: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Problem], str | None]: ...


class MockProblemRepository(ProblemRepository):
    def __init__(self) -> None:
        self._problems: list[Problem] = list(MOCK_PROBLEMS)

    async def get_by_id(self, entity_id: str) -> Problem | None:
        return next((p for p in self._problems if p.id == entity_id), None)

    async def get_by_slug(self, slug: str) -> Problem | None:
        return next((p for p in self._problems if p.slug == slug), None)

    async def list_paginated(
        self,
        difficulty: str | None = None,
        tag: str | None = None,
        q: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Problem], str | None]:
        items = [p for p in self._problems if p.is_public]
        if difficulty:
            items = [p for p in items if p.difficulty == difficulty]
        if tag:
            items = [p for p in items if tag in p.tags]
        if q:
            needle = q.lower()
            items = [p for p in items if needle in p.title.lower()]
        items.sort(key=lambda p: (p.created_at, p.id))

        if cursor:
            start = next((i + 1 for i, p in enumerate(items) if p.id == cursor), 0)
            items = items[start:]

        page = items[:limit]
        next_cursor = page[-1].id if len(items) > limit and page else None
        return page, next_cursor

    async def list_all(self, **filters: object) -> list[Problem]:
        return list(self._problems)

    async def create(self, entity: Problem) -> Problem:
        self._problems.append(entity)
        return entity

    async def update(self, entity: Problem) -> Problem:
        for i, p in enumerate(self._problems):
            if p.id == entity.id:
                self._problems[i] = entity
                return entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._problems)
        self._problems = [p for p in self._problems if p.id != entity_id]
        return len(self._problems) < before

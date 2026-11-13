from abc import abstractmethod

from app.models.interviewer import InterviewerTurn
from app.repositories.base import AbstractRepository


class InterviewerTurnRepository(AbstractRepository[InterviewerTurn]):
    @abstractmethod
    async def list_by_session(self, session_id: str) -> list[InterviewerTurn]:
        """Oldest first (by ordinal)."""
        ...

    @abstractmethod
    async def next_ordinal(self, session_id: str) -> int: ...

    @abstractmethod
    async def delete_by_session(self, session_id: str) -> int: ...


class MockInterviewerTurnRepository(InterviewerTurnRepository):
    def __init__(self) -> None:
        self._items: list[InterviewerTurn] = []

    async def get_by_id(self, entity_id: str) -> InterviewerTurn | None:
        return next((t for t in self._items if t.id == entity_id), None)

    async def list_by_session(self, session_id: str) -> list[InterviewerTurn]:
        mine = (t for t in self._items if t.session_id == session_id)
        return sorted(mine, key=lambda t: t.ordinal)

    async def next_ordinal(self, session_id: str) -> int:
        return max((t.ordinal for t in self._items if t.session_id == session_id), default=0) + 1

    async def delete_by_session(self, session_id: str) -> int:
        before = len(self._items)
        self._items = [t for t in self._items if t.session_id != session_id]
        return before - len(self._items)

    async def list_all(self, **filters: object) -> list[InterviewerTurn]:
        return list(self._items)

    async def create(self, entity: InterviewerTurn) -> InterviewerTurn:
        self._items.append(entity)
        return entity

    async def update(self, entity: InterviewerTurn) -> InterviewerTurn:
        for i, t in enumerate(self._items):
            if t.id == entity.id:
                self._items[i] = entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._items)
        self._items = [t for t in self._items if t.id != entity_id]
        return len(self._items) < before

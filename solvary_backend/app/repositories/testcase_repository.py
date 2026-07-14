from abc import abstractmethod

from app.mock_data.problems import MOCK_TESTCASES
from app.models.testcase import TestCase
from app.repositories.base import AbstractRepository


class TestCaseRepository(AbstractRepository[TestCase]):
    @abstractmethod
    async def list_by_problem(self, problem_id: str) -> list[TestCase]:
        """All cases for a problem, ordered by ordinal."""
        ...


class MockTestCaseRepository(TestCaseRepository):
    def __init__(self) -> None:
        self._cases: list[TestCase] = list(MOCK_TESTCASES)

    async def get_by_id(self, entity_id: str) -> TestCase | None:
        return next((c for c in self._cases if c.id == entity_id), None)

    async def list_by_problem(self, problem_id: str) -> list[TestCase]:
        return sorted(
            (c for c in self._cases if c.problem_id == problem_id),
            key=lambda c: c.ordinal,
        )

    async def list_all(self, **filters: object) -> list[TestCase]:
        return list(self._cases)

    async def create(self, entity: TestCase) -> TestCase:
        self._cases.append(entity)
        return entity

    async def update(self, entity: TestCase) -> TestCase:
        for i, c in enumerate(self._cases):
            if c.id == entity.id:
                self._cases[i] = entity
                return entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._cases)
        self._cases = [c for c in self._cases if c.id != entity_id]
        return len(self._cases) < before

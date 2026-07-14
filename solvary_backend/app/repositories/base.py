from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class AbstractRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_by_id(self, entity_id: str) -> T | None: ...

    @abstractmethod
    async def list_all(self, **filters: object) -> list[T]: ...

    @abstractmethod
    async def create(self, entity: T) -> T: ...

    @abstractmethod
    async def update(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, entity_id: str) -> bool: ...

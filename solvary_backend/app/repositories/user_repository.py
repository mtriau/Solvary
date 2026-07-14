from abc import abstractmethod

from app.mock_data.users import MOCK_USERS
from app.models.user import User
from app.repositories.base import AbstractRepository


class UserRepository(AbstractRepository[User]):
    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_google_sub(self, sub: str) -> User | None: ...


class MockUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: list[User] = list(MOCK_USERS)

    async def get_by_id(self, entity_id: str) -> User | None:
        return next((u for u in self._users if u.id == entity_id), None)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._users if u.email == email), None)

    async def get_by_google_sub(self, sub: str) -> User | None:
        return next((u for u in self._users if u.google_sub == sub), None)

    async def list_all(self, **filters: object) -> list[User]:
        return list(self._users)

    async def create(self, entity: User) -> User:
        self._users.append(entity)
        return entity

    async def update(self, entity: User) -> User:
        for i, u in enumerate(self._users):
            if u.id == entity.id:
                self._users[i] = entity
                return entity
        return entity

    async def delete(self, entity_id: str) -> bool:
        before = len(self._users)
        self._users = [u for u in self._users if u.id != entity_id]
        return len(self._users) < before

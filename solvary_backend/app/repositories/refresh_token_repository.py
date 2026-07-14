from abc import ABC, abstractmethod

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def get_by_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def create(self, token: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def revoke(self, token_id: str) -> None: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: str) -> int: ...


class MockRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self) -> None:
        self._tokens: list[RefreshToken] = []

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        return next((t for t in self._tokens if t.token_hash == token_hash), None)

    async def create(self, token: RefreshToken) -> RefreshToken:
        self._tokens.append(token)
        return token

    async def revoke(self, token_id: str) -> None:
        for t in self._tokens:
            if t.id == token_id:
                t.revoked = True

    async def revoke_all_for_user(self, user_id: str) -> int:
        n = 0
        for t in self._tokens:
            if t.user_id == user_id and not t.revoked:
                t.revoked = True
                n += 1
        return n

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import RefreshTokenRow
from app.models.refresh_token import RefreshToken
from app.repositories.refresh_token_repository import RefreshTokenRepository


class SQLAlchemyRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshTokenRow).where(RefreshTokenRow.token_hash == token_hash)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if not row:
            return None
        return RefreshToken(
            id=row.id,
            user_id=row.user_id,
            token_hash=row.token_hash,
            expires_at=row.expires_at,
            revoked=row.revoked,
            created_at=row.created_at,
        )

    async def create(self, token: RefreshToken) -> RefreshToken:
        self._session.add(
            RefreshTokenRow(
                id=token.id,
                user_id=token.user_id,
                token_hash=token.token_hash,
                expires_at=token.expires_at,
                revoked=token.revoked,
                created_at=token.created_at,
            )
        )
        await self._session.flush()
        return token

    async def revoke(self, token_id: str) -> None:
        await self._session.execute(
            update(RefreshTokenRow).where(RefreshTokenRow.id == token_id).values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: str) -> int:
        result = await self._session.execute(
            update(RefreshTokenRow)
            .where(RefreshTokenRow.user_id == user_id, RefreshTokenRow.revoked.is_(False))
            .values(revoked=True)
        )
        return result.rowcount or 0

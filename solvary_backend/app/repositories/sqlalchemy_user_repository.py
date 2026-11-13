from datetime import UTC, datetime

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.tables import UserRow
from app.models.user import User
from app.repositories.user_repository import UserRepository


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, entity_id: str) -> User | None:
        row = await self._session.get(UserRow, entity_id)
        return self._to_domain(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserRow).where(UserRow.email == email)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def get_by_google_sub(self, sub: str) -> User | None:
        stmt = select(UserRow).where(UserRow.google_sub == sub)
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def list_all(self, **filters: object) -> list[User]:
        stmt = select(UserRow).order_by(UserRow.created_at)
        result = await self._session.execute(stmt)
        return [self._to_domain(row) for row in result.scalars().all()]

    async def create(self, entity: User) -> User:
        row = UserRow(
            id=entity.id,
            name=entity.name,
            email=entity.email,
            hashed_password=entity.hashed_password,
            avatar_url=entity.avatar_url,
            role=entity.role,
            google_sub=entity.google_sub,
            anthropic_api_key_enc=entity.anthropic_api_key_enc,
            anthropic_api_key_last4=entity.anthropic_api_key_last4,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        self._session.add(row)
        await self._session.flush()
        return entity

    async def update(self, entity: User) -> User:
        row = await self._session.get(UserRow, entity.id)
        if row:
            row.name = entity.name
            row.email = entity.email
            row.hashed_password = entity.hashed_password
            row.avatar_url = entity.avatar_url
            row.role = entity.role
            row.google_sub = entity.google_sub
            row.anthropic_api_key_enc = entity.anthropic_api_key_enc
            row.anthropic_api_key_last4 = entity.anthropic_api_key_last4
            row.updated_at = datetime.now(UTC)
            await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> bool:
        stmt = sa_delete(UserRow).where(UserRow.id == entity_id)
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0

    @staticmethod
    def _to_domain(row: UserRow) -> User:
        return User(
            id=row.id,
            name=row.name,
            email=row.email,
            hashed_password=row.hashed_password,
            avatar_url=row.avatar_url,
            role=row.role,  # type: ignore[arg-type]
            google_sub=row.google_sub,
            anthropic_api_key_enc=row.anthropic_api_key_enc,
            anthropic_api_key_last4=row.anthropic_api_key_last4,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )

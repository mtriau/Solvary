"""Doc-repository provider for the collaboration manager — mirrors the
judge worker's repo provider: mock singleton vs fresh SQLAlchemy session."""

from contextlib import asynccontextmanager

from app.config import Settings


def make_auth_lookup(settings: Settings):
    """Short-lived (user, member) lookup for the WS endpoint — a Depends(get_db)
    session would stay open (and pin a pool slot) for the whole life of the
    WebSocket connection; this closes before the relay loop starts."""

    async def lookup(user_id: str, workspace_id: str):
        if settings.use_mock_db:
            from app.repositories.mock_registry import mock_member_repo, mock_user_repo

            user = await mock_user_repo.get_by_id(user_id)
            member = await mock_member_repo.get_by_workspace_and_user(
                workspace_id, user_id
            )
            return user, member

        from app.db.engine import async_session_factory
        from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
        from app.repositories.sqlalchemy_workspace_repository import (
            SQLAlchemyMemberRepository,
        )

        async with async_session_factory() as session:
            user = await SQLAlchemyUserRepository(session).get_by_id(user_id)
            member = await SQLAlchemyMemberRepository(session).get_by_workspace_and_user(
                workspace_id, user_id
            )
            return user, member

    return lookup


def make_doc_repo_provider(settings: Settings):
    if settings.use_mock_db:
        from app.repositories.mock_registry import mock_doc_repo

        @asynccontextmanager
        async def mock_provider():
            yield mock_doc_repo

        return mock_provider

    @asynccontextmanager
    async def sqlalchemy_provider():
        from app.db.engine import async_session_factory
        from app.repositories.sqlalchemy_doc_repository import SQLAlchemyDocRepository

        async with async_session_factory() as session:
            try:
                yield SQLAlchemyDocRepository(session)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    return sqlalchemy_provider

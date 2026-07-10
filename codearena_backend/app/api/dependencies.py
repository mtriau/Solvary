from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.exceptions import ForbiddenException
from app.models.user import User
from app.repositories.user_repository import MockUserRepository, UserRepository
from app.services.auth_service import AuthService
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ── Mock singletons (used when USE_MOCK_DB=true) ─────────────────

_mock_user_repo = MockUserRepository()


# ── DB session dependency ─────────────────────────────────────────


async def get_db(settings: Annotated[Settings, Depends(get_settings)]):
    """Yields a DB session when using real persistence, None for mock mode."""
    if settings.use_mock_db:
        yield None
    else:
        from app.db.engine import get_db_session

        async for session in get_db_session():
            yield session


# ── Repository providers ──────────────────────────────────────────


def get_user_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> UserRepository:
    if settings.use_mock_db:
        return _mock_user_repo
    from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

    assert db is not None
    return SQLAlchemyUserRepository(db)


# ── Service providers ─────────────────────────────────────────────


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(user_repo, settings)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


# ── Auth dependencies ─────────────────────────────────────────────


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return await auth_service.get_current_user(token)


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise ForbiddenException("Admin privileges required")
    return current_user

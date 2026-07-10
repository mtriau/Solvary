import uuid
from datetime import UTC, datetime

from app.config import Settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.users import UserResponse


class AuthService:
    def __init__(self, user_repo: UserRepository, settings: Settings) -> None:
        self._user_repo = user_repo
        self._settings = settings

    async def register(self, name: str, email: str, password: str) -> TokenResponse:
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise ConflictException("A user with this email already exists")

        user = User(
            id=f"user_{uuid.uuid4().hex[:8]}",
            name=name,
            email=email,
            hashed_password=hash_password(password),
            avatar_url=f"https://api.dicebear.com/9.x/initials/svg?seed={name[:2].upper()}",
            role="user",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        await self._user_repo.create(user)
        token = create_access_token({"sub": user.id})
        return TokenResponse(
            access_token=token,
            user=self._to_user_response(user),
        )

    async def login(self, email: str, password: str) -> TokenResponse:
        user = await self._user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        token = create_access_token({"sub": user.id})
        return TokenResponse(
            access_token=token,
            user=self._to_user_response(user),
        )

    async def get_current_user(self, token: str) -> User:
        try:
            payload = decode_access_token(token)
        except ValueError as e:
            raise UnauthorizedException(str(e)) from e

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Invalid token payload")

        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise UnauthorizedException("User not found")
        return user

    @staticmethod
    def _to_user_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            role=user.role,
        )

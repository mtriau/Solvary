import uuid
from datetime import UTC, datetime, timedelta

from app.config import Settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.google_oauth import verify_google_id_token
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse
from app.schemas.users import UserResponse


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        refresh_repo: RefreshTokenRepository,
        settings: Settings,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_repo = refresh_repo
        self._settings = settings

    # ── local accounts ─────────────────────────────────────────────

    async def register(self, name: str, email: str, password: str) -> tuple[TokenResponse, str]:
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
        )
        await self._user_repo.create(user)
        return await self._issue_tokens(user)

    async def login(self, email: str, password: str) -> tuple[TokenResponse, str]:
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedException("Invalid email or password")
        if not user.hashed_password:
            # Google-created account with no local password
            raise UnauthorizedException("This account signs in with Google")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        return await self._issue_tokens(user)

    # ── Google OIDC (design decision: verified email required) ────

    async def google_login(self, credential: str) -> tuple[TokenResponse, str]:
        if not self._settings.google_client_id:
            raise UnauthorizedException("Google sign-in is not configured")

        claims = await verify_google_id_token(credential, self._settings.google_client_id)
        sub, email = claims["sub"], claims["email"]

        user = await self._user_repo.get_by_google_sub(sub)
        if user is None:
            # Auto-link by verified email, else create a passwordless account
            user = await self._user_repo.get_by_email(email)
            if user is None:
                user = User(
                    id=f"user_{uuid.uuid4().hex[:8]}",
                    name=claims.get("name") or email.split("@")[0],
                    email=email,
                    hashed_password="",  # signs in with Google only
                    avatar_url=claims.get("picture")
                    or f"https://api.dicebear.com/9.x/initials/svg?seed={email[:2].upper()}",
                    role="user",
                    google_sub=sub,
                )
                await self._user_repo.create(user)
            else:
                user.google_sub = sub
                await self._user_repo.update(user)
        return await self._issue_tokens(user)

    # ── refresh-token lifecycle ────────────────────────────────────

    async def refresh(self, raw_refresh_token: str) -> tuple[TokenResponse, str]:
        """Rotate: validate → revoke the presented token → issue new pair."""
        record = await self._get_valid_refresh(raw_refresh_token)
        user = await self._user_repo.get_by_id(record.user_id)
        if not user:
            raise UnauthorizedException("User not found")
        await self._refresh_repo.revoke(record.id)
        return await self._issue_tokens(user)

    async def logout(self, raw_refresh_token: str | None) -> None:
        """Revoke the presented refresh token (idempotent, never errors)."""
        if not raw_refresh_token:
            return
        record = await self._refresh_repo.get_by_hash(
            hash_refresh_token(raw_refresh_token)
        )
        if record and not record.revoked:
            await self._refresh_repo.revoke(record.id)

    async def _get_valid_refresh(self, raw: str) -> RefreshToken:
        record = await self._refresh_repo.get_by_hash(hash_refresh_token(raw))
        if record is None or record.revoked:
            raise UnauthorizedException("Invalid refresh token")
        expires_at = record.expires_at
        if expires_at.tzinfo is None:  # SQLite returns naive datetimes
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise UnauthorizedException("Refresh token expired")
        return record

    async def _issue_tokens(self, user: User) -> tuple[TokenResponse, str]:
        raw_refresh, token_hash = generate_refresh_token()
        await self._refresh_repo.create(
            RefreshToken(
                id=f"rt_{uuid.uuid4().hex[:8]}",
                user_id=user.id,
                token_hash=token_hash,
                expires_at=datetime.now(UTC)
                + timedelta(days=self._settings.refresh_token_expire_days),
            )
        )
        access = create_access_token({"sub": user.id})
        return (
            TokenResponse(access_token=access, user=self._to_user_response(user)),
            raw_refresh,
        )

    # ── access tokens (unchanged) ──────────────────────────────────

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

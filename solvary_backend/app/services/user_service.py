from app.config import Settings, get_settings
from app.core.exceptions import BadRequestException, NotFoundException, PaymentRequiredException
from app.core.secrets import encrypt_secret, secret_last4
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.interviewer import AiKeyStatus, AiKeyTestResult
from app.schemas.users import UserResponse
from app.services.ai_keys import key_status, resolve_api_key
from app.services.claude_client import ClaudeClient, ClaudeError


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        settings: Settings | None = None,
        claude: ClaudeClient | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._settings = settings or get_settings()
        self._claude = claude

    async def get_by_id(self, user_id: str) -> UserResponse:
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return self._to_response(user)

    async def get_me(self, current_user: User) -> UserResponse:
        return self._to_response(current_user)

    # ── Anthropic API key (interviewer agent) ─────────────────────
    # The raw key is never returned by any endpoint; only its last 4 chars.

    async def get_ai_key_status(self, user: User) -> AiKeyStatus:
        return key_status(user, self._settings)

    async def set_ai_key(self, user: User, api_key: str) -> AiKeyStatus:
        user.anthropic_api_key_enc = encrypt_secret(api_key)
        user.anthropic_api_key_last4 = secret_last4(api_key)
        await self._user_repo.update(user)
        return key_status(user, self._settings)

    async def clear_ai_key(self, user: User) -> AiKeyStatus:
        user.anthropic_api_key_enc = None
        user.anthropic_api_key_last4 = None
        await self._user_repo.update(user)
        return key_status(user, self._settings)

    async def test_ai_key(self, user: User) -> AiKeyTestResult:
        """One tiny request on whichever key the interviewer would use."""
        if self._claude is None:
            raise BadRequestException("The interviewer agent is not configured on this server")
        key, source = resolve_api_key(user, self._settings)
        if not key:
            raise PaymentRequiredException("No Anthropic API key configured")
        try:
            model = await self._claude.ping(key, self._settings.interviewer_model)
        except ClaudeError as e:
            raise BadRequestException(e.detail) from e
        return AiKeyTestResult(ok=True, model=model, source=source)

    @staticmethod
    def _to_response(user: User) -> UserResponse:
        return UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            avatar_url=user.avatar_url,
            role=user.role,
        )

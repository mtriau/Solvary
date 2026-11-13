"""Which Anthropic key does a request use? The user's (encrypted at rest),
else the server's, else none (→ 402 NO_API_KEY)."""

import logging

from app.config import Settings
from app.core.secrets import InvalidToken, decrypt_secret
from app.models.user import User
from app.schemas.interviewer import AiKeyStatus, KeySource

logger = logging.getLogger(__name__)


def resolve_api_key(user: User, settings: Settings) -> tuple[str | None, KeySource]:
    if user.anthropic_api_key_enc:
        try:
            return decrypt_secret(user.anthropic_api_key_enc), "user"
        except InvalidToken:
            logger.warning(
                "Stored API key for user %s cannot be decrypted (SECRET_KEY changed?)", user.id
            )
    if settings.anthropic_api_key:
        return settings.anthropic_api_key, "server"
    return None, "none"


def key_status(user: User, settings: Settings) -> AiKeyStatus:
    key, source = resolve_api_key(user, settings)
    if source == "user":
        return AiKeyStatus(configured=True, last4=user.anthropic_api_key_last4, source="user")
    if source == "server":
        return AiKeyStatus(configured=True, last4=key[-4:] if key else None, source="server")
    return AiKeyStatus(configured=False, last4=None, source="none")

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal


@dataclass
class User:
    id: str
    name: str
    email: str
    hashed_password: str
    avatar_url: str
    role: Literal["user", "admin"] = "user"
    google_sub: str | None = None  # Google account id when linked via OIDC
    # Interviewer agent: Anthropic key encrypted at rest (core/secrets.py) + a hint
    anthropic_api_key_enc: str | None = None
    anthropic_api_key_last4: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

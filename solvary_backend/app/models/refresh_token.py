from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class RefreshToken:
    """Server-side record of a refresh token. Only the SHA-256 hash is
    stored — a DB leak must not yield usable tokens. Rotation: each use
    revokes the row and issues a new one."""

    id: str
    user_id: str
    token_hash: str
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

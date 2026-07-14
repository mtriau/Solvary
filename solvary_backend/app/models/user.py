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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

from app.core.security import hash_password
from app.models.user import User

# All mock users share the same password: "password123"
_MOCK_PASSWORD_HASH = hash_password("password123")

MOCK_USERS: list[User] = [
    User(
        id="user_admin",
        name="Arena Admin",
        email="admin@codearena.dev",
        hashed_password=_MOCK_PASSWORD_HASH,
        avatar_url="https://api.dicebear.com/9.x/initials/svg?seed=AA",
        role="admin",
    ),
    User(
        id="user_matt",
        name="Matt Triau",
        email="matt@codearena.dev",
        hashed_password=_MOCK_PASSWORD_HASH,
        avatar_url="https://api.dicebear.com/9.x/initials/svg?seed=MT",
        role="user",
    ),
    User(
        id="user_alice",
        name="Alice Chen",
        email="alice@codearena.dev",
        hashed_password=_MOCK_PASSWORD_HASH,
        avatar_url="https://api.dicebear.com/9.x/initials/svg?seed=AC",
        role="user",
    ),
]

MOCK_USERS_MAP: dict[str, User] = {u.id: u for u in MOCK_USERS}

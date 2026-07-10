"""
Seed an admin user into the real database.

Usage:
    python -m scripts.seed_admin [email] [password] [name]

Defaults: admin@codearena.dev / admin123 / "Arena Admin".
Idempotent: if the email already exists, the user is promoted to admin instead.
"""

import asyncio
import sys
import uuid

import app.db.tables  # noqa: F401 — register tables with Base.metadata
from app.core.security import hash_password
from app.db.base import Base
from app.db.engine import async_session_factory, engine
from app.models.user import User
from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository


async def seed(email: str, password: str, name: str) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)
        existing = await repo.get_by_email(email)
        if existing:
            if existing.role == "admin":
                print(f"Admin already exists: {existing.id} <{email}>")
            else:
                existing.role = "admin"
                await repo.update(existing)
                print(f"Promoted existing user to admin: {existing.id} <{email}>")
        else:
            user = User(
                id=f"user_{uuid.uuid4().hex[:8]}",
                name=name,
                email=email,
                hashed_password=hash_password(password),
                avatar_url=f"https://api.dicebear.com/9.x/initials/svg?seed={name[:2].upper()}",
                role="admin",
            )
            await repo.create(user)
            print(f"Created admin: {user.id} <{email}>")
        await session.commit()

    await engine.dispose()


if __name__ == "__main__":
    args = sys.argv[1:]
    email = args[0] if len(args) > 0 else "admin@codearena.dev"
    password = args[1] if len(args) > 1 else "admin123"
    name = args[2] if len(args) > 2 else "Arena Admin"
    asyncio.run(seed(email, password, name))

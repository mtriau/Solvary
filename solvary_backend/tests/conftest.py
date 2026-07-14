"""
Test bootstrap — ISOLATION FIRST.

The engine and settings are created at import time, so the test environment
must be injected before ANY app import. Tests never touch the dev database:
they run against solvary_test.db (or $TEST_DATABASE_URL — CI points this at
Postgres), with a schema rebuilt fresh each session and a seeded admin.
"""

import asyncio
import os

# ── environment BEFORE app imports ────────────────────────────────
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "sqlite+aiosqlite:///./solvary_test.db"
)
os.environ["USE_MOCK_DB"] = "false"
os.environ["EXECUTION_PROVIDER"] = "mock"  # judge tests rely on mock markers
os.environ["SECRET_KEY"] = "test-secret-not-for-production"
os.environ["DB_NULL_POOL"] = "true"  # per-test event loops (see engine.py)

import uuid  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services.queue import runtime as runtime_module  # noqa: E402
from app.services.queue.runtime import ExecutionRuntime  # noqa: E402

TEST_ADMIN_EMAIL = "admin@solvary.dev"
TEST_ADMIN_PASSWORD = "admin123"


@pytest.fixture(scope="session", autouse=True)
def _fresh_test_database():
    """Drop + recreate the schema and seed the admin, once per session.

    Runs in a throwaway event loop; the engine is disposed afterwards so no
    loop-bound connection leaks into the tests' own loops.
    """

    async def setup() -> None:
        import app.db.tables  # noqa: F401 — register tables with Base.metadata
        from app.core.security import hash_password
        from app.db.base import Base
        from app.db.engine import async_session_factory, engine
        from app.models.user import User
        from app.repositories.sqlalchemy_user_repository import (
            SQLAlchemyUserRepository,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async with async_session_factory() as session:
            await SQLAlchemyUserRepository(session).create(
                User(
                    id=f"user_{uuid.uuid4().hex[:8]}",
                    name="Test Admin",
                    email=TEST_ADMIN_EMAIL,
                    hashed_password=hash_password(TEST_ADMIN_PASSWORD),
                    avatar_url="",
                    role="admin",
                )
            )
            await session.commit()

        await engine.dispose()

    assert "solvary.db" not in os.environ["DATABASE_URL"].replace(
        "solvary_test.db", ""
    ), "tests must never point at the dev database"
    asyncio.run(setup())
    yield


@pytest.fixture
async def judge_runtime():
    """Fresh execution runtime bound to this test's event loop.

    ASGITransport does not run the app lifespan, so the worker tasks that
    normally start there are started (and torn down) here instead.
    """
    runtime = ExecutionRuntime(get_settings())
    runtime_module._runtime = runtime
    await runtime.start()
    yield runtime
    await runtime.stop()
    runtime_module._runtime = None


@pytest.fixture
async def client(judge_runtime):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── shared fixtures ────────────────────────────────────────────────

TWO_SUM_CASES = [
    {"ordinal": 1, "stdin": "4 9\n2 7 11 15\n", "expected_stdout": "0 1\n", "is_sample": True},
    {"ordinal": 2, "stdin": "3 6\n3 2 4\n", "expected_stdout": "1 2\n", "is_sample": True},
    {"ordinal": 3, "stdin": "2 6\n3 3\n", "expected_stdout": "0 1\n", "is_sample": False},
    {"ordinal": 4, "stdin": "5 0\n-3 4 3 90 1\n", "expected_stdout": "0 2\n", "is_sample": False},
]


async def ensure_two_sum(client: AsyncClient) -> dict:
    """Get-or-create the canonical two-sum problem (4 cases, 2 sample) in the
    ISOLATED test DB — tests must never assume dev seed data exists."""
    resp = await client.get("/api/v1/problems/two-sum")
    if resp.status_code == 200:
        return resp.json()

    resp = await client.post(
        "/api/auth/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

    resp = await client.post(
        "/api/v1/problems",
        json={
            "slug": "two-sum",
            "title": "Two Sum",
            "difficulty": "easy",
            "statement_md": "Print the indices of the two numbers adding to target.",
            "starter_code": {"python": "# starter\n", "javascript": "// starter\n"},
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    problem = resp.json()
    for case in TWO_SUM_CASES:
        resp = await client.post(
            f"/api/v1/problems/{problem['id']}/testcases", json=case, headers=headers
        )
        assert resp.status_code == 201, resp.text
    return problem

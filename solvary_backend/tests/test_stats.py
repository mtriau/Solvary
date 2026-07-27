"""Stats + accolades: totals, difficulty, streak math, badges."""

import uuid
from datetime import UTC, date, datetime, timedelta

from httpx import AsyncClient

from app.services.stats_service import _streaks

ADMIN = {"email": "admin@solvary.dev", "password": "admin123"}


async def _login(client, email, password) -> dict:
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _register(client, name) -> dict:
    email = f"{name}-{uuid.uuid4().hex[:8]}@test.dev"
    r = await client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": "pw123456"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _make_problem(client, admin_h, difficulty="easy") -> dict:
    slug = f"stat-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/problems",
        json={
            "slug": slug,
            "title": f"Stats {slug}",
            "difficulty": difficulty,
            "statement_md": "x",
            "starter_code": {"python": ""},
        },
        headers=admin_h,
    )
    problem = r.json()
    await client.post(
        f"/api/v1/problems/{problem['id']}/testcases",
        json={"ordinal": 1, "stdin": "a\n", "expected_stdout": "a\n", "is_sample": True},
        headers=admin_h,
    )
    return problem


async def _submit_and_wait(client, headers, problem_id, code="ok") -> str:
    r = await client.post(
        "/api/v1/submissions",
        json={"problem_id": problem_id, "language": "python", "code": code},
        headers=headers,
    )
    sub_id = r.json()["id"]
    for _ in range(100):
        r = await client.get(f"/api/v1/submissions/{sub_id}", headers=headers)
        if r.json()["verdict"] not in ("queued", "running"):
            return r.json()["verdict"]
        import asyncio

        await asyncio.sleep(0.05)
    raise AssertionError("verdict never arrived")


# ── streak math (pure) ─────────────────────────────────────────────


def test_streaks_empty():
    assert _streaks(set()) == (0, 0)


def test_streaks_current_and_longest():
    today = datetime.now(UTC).date()
    days = {today, today - timedelta(days=1)}  # current run of 2
    days |= {date(2026, 1, 1) + timedelta(days=i) for i in range(5)}  # old run of 5
    current, longest = _streaks(days)
    assert current == 2
    assert longest == 5


def test_streak_alive_via_yesterday():
    yesterday = datetime.now(UTC).date() - timedelta(days=1)
    current, longest = _streaks({yesterday})
    assert current == 1 and longest == 1


# ── endpoint ───────────────────────────────────────────────────────


async def test_stats_flow(client: AsyncClient):
    admin_h = await _login(client, **ADMIN)
    user_h = await _register(client, "statsuser")

    easy = await _make_problem(client, admin_h, "easy")
    hard = await _make_problem(client, admin_h, "hard")

    # Fail twice on easy (WA), then solve it; solve is on first try for hard
    assert await _submit_and_wait(client, user_h, easy["id"], "x __MOCK_WA__") == "wrong_answer"
    assert await _submit_and_wait(client, user_h, easy["id"], "x __MOCK_WA__") == "wrong_answer"
    assert await _submit_and_wait(client, user_h, easy["id"]) == "accepted"
    assert await _submit_and_wait(client, user_h, hard["id"]) == "accepted"

    r = await client.get("/api/v1/stats/me", headers=user_h)
    assert r.status_code == 200
    stats = r.json()

    totals = stats["totals"]
    assert totals["submissions"] == 4
    assert totals["accepted_submissions"] == 2
    assert totals["solved"] == 2
    assert totals["acceptance_rate"] == 0.5
    assert totals["current_streak_days"] >= 1

    by_diff = {d["difficulty"]: d for d in stats["by_difficulty"]}
    assert by_diff["easy"]["solved"] == 1
    assert by_diff["hard"]["solved"] == 1
    assert by_diff["medium"]["solved"] == 0

    langs = {lang["language"]: lang for lang in stats["by_language"]}
    assert langs["python"]["submissions"] == 4
    assert langs["python"]["solved"] == 2

    # Heatmap: today registers all 4 submissions, list covers 182 days
    assert len(stats["heatmap"]) == 182
    assert stats["heatmap"][-1]["count"] == 4

    badges = {b["id"]: b["earned"] for b in stats["badges"]}
    assert badges["first-blood"] is True
    assert badges["one-shot"] is True        # hard solved on first attempt
    assert badges["comeback-kid"] is False   # only 2 fails before accept
    assert badges["century"] is False
    assert badges["pair-programmer"] is False

    # Recent activity: newest first, includes problem metadata
    assert stats["recent"][0]["problem_slug"] == hard["slug"]
    assert stats["recent"][0]["verdict"] == "accepted"
    assert len(stats["recent"]) == 4


async def test_stats_empty_user(client: AsyncClient):
    user_h = await _register(client, "freshuser")
    r = await client.get("/api/v1/stats/me", headers=user_h)
    assert r.status_code == 200
    stats = r.json()
    assert stats["totals"]["submissions"] == 0
    assert stats["totals"]["acceptance_rate"] == 0.0
    assert all(not b["earned"] for b in stats["badges"])
    assert stats["recent"] == []

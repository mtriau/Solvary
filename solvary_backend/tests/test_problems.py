import uuid

import pytest
from httpx import AsyncClient

ADMIN = {"email": "admin@solvary.dev", "password": "admin123"}


async def _login(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _register_user(client: AsyncClient) -> str:
    email = f"prob_{uuid.uuid4().hex[:8]}@solvary.dev"
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Problem Tester", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_problems_public(client: AsyncClient):
    resp = await client.get("/api/v1/problems")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(p["slug"] == "two-sum" for p in items)
    # summaries never contain statements or test cases
    assert "statement_md" not in items[0]


@pytest.mark.asyncio
async def test_get_problem_detail_hides_hidden_cases(client: AsyncClient):
    resp = await client.get("/api/v1/problems/two-sum")
    assert resp.status_code == 200
    body = resp.json()
    assert body["title"] == "Two Sum"
    assert "python" in body["starter_code"]
    # two-sum has 4 cases, 2 of them samples — only samples serialized
    assert len(body["sample_testcases"]) == 2


@pytest.mark.asyncio
async def test_difficulty_filter(client: AsyncClient):
    resp = await client.get("/api/v1/problems?difficulty=hard")
    assert resp.status_code == 200
    assert all(p["difficulty"] == "hard" for p in resp.json()["items"])


@pytest.mark.asyncio
async def test_problem_create_requires_admin(client: AsyncClient):
    user_token = await _register_user(client)
    payload = {
        "slug": f"test-{uuid.uuid4().hex[:6]}",
        "title": "Test Problem",
        "difficulty": "easy",
        "statement_md": "Do the thing.",
    }
    resp = await client.post("/api/v1/problems", json=payload, headers=_auth(user_token))
    assert resp.status_code == 403

    admin_token = await _login(client, **ADMIN)
    resp = await client.post("/api/v1/problems", json=payload, headers=_auth(admin_token))
    assert resp.status_code == 201
    assert resp.json()["slug"] == payload["slug"]


@pytest.mark.asyncio
async def test_testcases_admin_only(client: AsyncClient):
    problems = (await client.get("/api/v1/problems?q=Two+Sum")).json()["items"]
    prob_id = problems[0]["id"]

    user_token = await _register_user(client)
    resp = await client.get(f"/api/v1/problems/{prob_id}/testcases", headers=_auth(user_token))
    assert resp.status_code == 403

    admin_token = await _login(client, **ADMIN)
    resp = await client.get(f"/api/v1/problems/{prob_id}/testcases", headers=_auth(admin_token))
    assert resp.status_code == 200
    cases = resp.json()
    assert len(cases) == 4  # admin sees hidden cases too
    assert any(not c["is_sample"] for c in cases)

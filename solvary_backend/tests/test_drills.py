"""
Drills API: topic grouping, per-user progress from submissions, navigation,
and the drills staying out of the public problem list.
"""

import asyncio
import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD

pytestmark = pytest.mark.asyncio


async def _headers(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/auth/login", json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _make_drill(client: AsyncClient, h: dict, topic: str, order: int) -> dict:
    module = f"m{uuid.uuid4().hex[:6]}"
    test_src = f"from {module} import f\n\n\ndef test_a():\n    assert f() == 1\n"
    resp = await client.post(
        "/api/v1/problems",
        json={
            "slug": f"drill-{module}",
            "title": f"Drill {module}",
            "difficulty": "easy",
            "statement_md": "Return 1.",
            "tags": ["drill", f"topic:{topic}", f"order:{order:02d}", "pytest"],
            "starter_code": {"python": "def f():\n    raise NotImplementedError\n"},
            "judge_mode": "pytest",
            "harness": {"module": module, "files": {f"test_{module}.py": test_src}},
            "editorial_md": "### Why\n\nBecause.\n",
            "is_public": False,
        },
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    problem = resp.json()
    resp = await client.post(
        f"/api/v1/problems/{problem['id']}/testcases",
        json={
            "ordinal": 1,
            "stdin": f"test_{module}.py::test_a",
            "expected_stdout": "PASS\n",
            "is_sample": True,
        },
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    return problem


async def _solve(client: AsyncClient, h: dict, problem_id: str) -> None:
    resp = await client.post(
        "/api/v1/submissions",
        json={"problem_id": problem_id, "language": "python", "code": "def f():\n    return 1\n"},
        headers=h,
    )
    assert resp.status_code == 201, resp.text
    sub_id = resp.json()["id"]
    for _ in range(200):
        body = (await client.get(f"/api/v1/submissions/{sub_id}", headers=h)).json()
        if body["verdict"] not in ("queued", "running"):
            assert body["verdict"] == "accepted", body
            return
        await asyncio.sleep(0.05)
    raise AssertionError("verdict never arrived")


async def test_list_groups_by_topic_and_tracks_progress(client: AsyncClient):
    h = await _headers(client)
    a = await _make_drill(client, h, "comprehensions", 1)
    b = await _make_drill(client, h, "comprehensions", 2)
    c = await _make_drill(client, h, "strings", 1)
    mine = {a["slug"], b["slug"], c["slug"]}

    resp = await client.get("/api/v1/drills", headers=h)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    by_topic = {t["slug"]: t for t in body["topics"]}
    assert [t["slug"] for t in body["topics"]].index("comprehensions") < [
        t["slug"] for t in body["topics"]
    ].index("strings")
    comp = [d for d in by_topic["comprehensions"]["drills"] if d["slug"] in mine]
    assert [d["slug"] for d in comp] == [a["slug"], b["slug"]]
    assert all(d["solved"] is False and d["attempts"] == 0 for d in comp)
    assert by_topic["comprehensions"]["title"] == "Comprehensions"

    # detail: editorial, provided tests, navigation
    resp = await client.get(f"/api/v1/drills/{a['slug']}", headers=h)
    assert resp.status_code == 200, resp.text
    detail = resp.json()
    assert detail["editorial_md"].startswith("### Why")
    assert detail["harness_files"] and list(detail["harness_files"]) == [f"test_{a['slug'][6:]}.py"]
    assert detail["topic"] == "comprehensions" and detail["topic_title"] == "Comprehensions"
    assert detail["solved"] is False and detail["attempts"] == 0
    assert detail["next_slug"] == b["slug"]
    assert detail["position"] >= 1 and detail["topic_total"] >= 2
    assert detail["sample_testcases"][0]["stdin"].endswith("::test_a")

    # the drill stays out of the public catalogue
    assert (await client.get(f"/api/v1/problems/{a['slug']}", headers=h)).status_code == 404
    listed = (await client.get("/api/v1/problems?limit=100", headers=h)).json()["items"]
    assert not any(p["slug"] in mine for p in listed)

    # solving flips progress; next_unsolved skips solved drills
    await _solve(client, h, a["id"])
    detail = (await client.get(f"/api/v1/drills/{a['slug']}", headers=h)).json()
    assert detail["solved"] is True and detail["attempts"] == 1
    assert detail["next_unsolved_slug"] == b["slug"]
    body = (await client.get("/api/v1/drills", headers=h)).json()
    comp = {d["slug"]: d for d in body["topics"][0]["drills"]}
    assert comp[a["slug"]]["solved"] is True
    assert comp[b["slug"]]["solved"] is False
    assert body["solved"] >= 1


async def test_unknown_drill_is_404(client: AsyncClient):
    h = await _headers(client)
    assert (await client.get("/api/v1/drills/nope", headers=h)).status_code == 404


async def test_drills_require_auth(client: AsyncClient):
    assert (await client.get("/api/v1/drills")).status_code == 401

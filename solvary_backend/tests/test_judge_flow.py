"""
End-to-end judge pipeline tests: submit → queue → worker → checker →
incremental persistence → SSE replay-then-follow. MockExecutor magic
markers steer outcomes (see app/services/execution/mock_executor.py).
"""

import asyncio
import json
import uuid

import pytest
from httpx import AsyncClient

from tests.conftest import ensure_two_sum

ADMIN = {"email": "admin@solvary.dev", "password": "admin123"}


async def _token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def _register(client: AsyncClient) -> str:
    email = f"judge_{uuid.uuid4().hex[:8]}@solvary.dev"
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Judge Tester", "email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _submit(client: AsyncClient, token: str, code: str) -> str:
    problem = await ensure_two_sum(client)
    resp = await client.post(
        "/api/v1/submissions",
        json={"problem_id": problem["id"], "language": "python", "code": code},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _wait_for_verdict(client: AsyncClient, token: str, sub_id: str) -> dict:
    for _ in range(100):
        body = (await client.get(f"/api/v1/submissions/{sub_id}", headers=_auth(token))).json()
        if body["verdict"] not in ("queued", "running"):
            return body
        await asyncio.sleep(0.05)
    raise AssertionError("verdict never became terminal")


async def _sse_events(client: AsyncClient, token: str, url: str) -> list[dict]:
    events = []
    async with client.stream("GET", url, headers=_auth(token)) as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
                if events[-1].get("kind") in ("verdict", "error"):
                    break
    return events


@pytest.mark.asyncio
async def test_accepted_flow_with_sse(client: AsyncClient):
    token = await _register(client)
    sub_id = await _submit(client, token, "print('mock accepted')")

    events = await _sse_events(client, token, f"/api/v1/submissions/{sub_id}/events")
    kinds = [e["kind"] for e in events]
    assert kinds[0] == "queued"
    assert "case_result" in kinds
    assert kinds[-1] == "verdict"

    final = events[-1]
    assert final["verdict"] == "accepted"
    assert final["passed"] == final["total"] == 4

    # Persisted state matches the stream
    body = await _wait_for_verdict(client, token, sub_id)
    assert body["verdict"] == "accepted"
    assert body["passed"] == 4
    assert len(body["test_results"]) == 4


@pytest.mark.asyncio
async def test_wrong_answer_stops_hidden_cases(client: AsyncClient):
    token = await _register(client)
    # __MOCK_WA__ corrupts the highest-ordinal case (a hidden one for two-sum)
    sub_id = await _submit(client, token, "print('x')  # __MOCK_WA__")
    body = await _wait_for_verdict(client, token, sub_id)
    assert body["verdict"] == "wrong_answer"
    assert body["passed"] == body["total"] - 1


@pytest.mark.asyncio
async def test_tle_verdict(client: AsyncClient):
    token = await _register(client)
    # Ordinal 1 is a sample: it fails as tle, remaining sample (ordinal 2)
    # still runs, hidden cases are skipped (§6.3)
    sub_id = await _submit(client, token, "while True: pass  # __MOCK_TLE__")
    body = await _wait_for_verdict(client, token, sub_id)
    assert body["verdict"] == "tle"
    statuses = {r["ordinal"]: r["status"] for r in body["test_results"]}
    assert statuses[1] == "tle"
    assert statuses[2] == "passed"  # remaining sample ran
    assert 3 not in statuses and 4 not in statuses  # hidden skipped


@pytest.mark.asyncio
async def test_compile_error(client: AsyncClient):
    token = await _register(client)
    sub_id = await _submit(client, token, "def f(:  # __MOCK_CE__")
    body = await _wait_for_verdict(client, token, sub_id)
    assert body["verdict"] == "compile_error"
    assert body["passed"] == 0


@pytest.mark.asyncio
async def test_sse_replay_after_terminal(client: AsyncClient):
    """A subscriber arriving after the judge finished replays everything
    from the persisted row (M1 DoD: verdict survives a page reload)."""
    token = await _register(client)
    sub_id = await _submit(client, token, "print('late subscriber')")
    await _wait_for_verdict(client, token, sub_id)

    events = await _sse_events(client, token, f"/api/v1/submissions/{sub_id}/events")
    kinds = [e["kind"] for e in events]
    assert kinds[0] == "queued"
    assert kinds.count("case_result") == 4
    assert kinds[-1] == "verdict"
    assert events[-1]["verdict"] == "accepted"


@pytest.mark.asyncio
async def test_submission_not_readable_by_stranger(client: AsyncClient):
    owner = await _register(client)
    stranger = await _register(client)
    sub_id = await _submit(client, owner, "print('private')")
    resp = await client.get(f"/api/v1/submissions/{sub_id}", headers=_auth(stranger))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_adhoc_run_stream(client: AsyncClient):
    token = await _register(client)
    resp = await client.post(
        "/api/v1/execution/run",
        json={"language": "python", "code": "print(1)", "stdin": "hello"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]

    events = await _sse_events(client, token, f"/api/v1/execution/{run_id}/events")
    result = next(e for e in events if e["kind"] == "case_result")
    assert result["stdout"] == "hello"  # mock echoes stdin
    assert events[-1]["verdict"] == "finished"


@pytest.mark.asyncio
async def test_unsupported_language_rejected(client: AsyncClient):
    token = await _register(client)
    problem = await ensure_two_sum(client)
    resp = await client.post(
        "/api/v1/submissions",
        json={"problem_id": problem["id"], "language": "cobol", "code": "x"},
        headers=_auth(token),
    )
    assert resp.status_code == 400

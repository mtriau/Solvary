"""Execution quota + ad-hoc run endpoint: rejected requests must not consume
concurrency slots (regression: two 400s used to lock a user out with 429),
workspace-tagged runs enforce editor RBAC, unknown run ids 404."""

import json
import uuid

from httpx import AsyncClient

from tests.conftest import ensure_two_sum

ADMIN = {"email": "admin@solvary.dev", "password": "admin123"}


async def _register(client: AsyncClient, name: str = "quota") -> tuple[str, dict]:
    email = f"{name}-{uuid.uuid4().hex[:8]}@test.dev"
    r = await client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": "pw123456"}
    )
    assert r.status_code == 201, r.text
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _sse(client: AsyncClient, headers: dict, url: str) -> list[dict]:
    """Drain a judge/run stream to its terminal event. Tests must not leave
    jobs in flight: the runtime teardown cancels workers mid-DB-write and
    aiosqlite's thread then trips over the closed loop."""
    events = []
    async with client.stream("GET", url, headers=headers) as resp:
        assert resp.status_code == 200, await resp.aread()
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
                if events[-1].get("kind") in ("verdict", "error"):
                    break
    return events


# ── quota slot release ─────────────────────────────────────────────


async def test_rejected_submissions_do_not_consume_quota(client: AsyncClient):
    _, h = await _register(client)
    problem = await ensure_two_sum(client)

    # More rejections than the concurrency limit (2): all must stay 400
    for _ in range(4):
        r = await client.post(
            "/api/v1/submissions",
            json={"problem_id": problem["id"], "language": "cobol", "code": "x"},
            headers=h,
        )
        assert r.status_code == 400, r.text

    # Body validation errors (422) are raised before the handler runs —
    # the yield dependency must release on those too
    for _ in range(3):
        r = await client.post("/api/v1/submissions", json={"nope": True}, headers=h)
        assert r.status_code == 422, r.text

    # Unknown problem (404) likewise
    r = await client.post(
        "/api/v1/submissions",
        json={"problem_id": "prob_nope", "language": "python", "code": "x"},
        headers=h,
    )
    assert r.status_code == 404

    # A valid submission still goes through — no leaked slots
    r = await client.post(
        "/api/v1/submissions",
        json={"problem_id": problem["id"], "language": "python", "code": "print(1)"},
        headers=h,
    )
    assert r.status_code == 201, r.text
    events = await _sse(client, h, f"/api/v1/submissions/{r.json()['id']}/events")
    assert events[-1]["verdict"] == "accepted"


async def test_rejected_runs_do_not_consume_quota(client: AsyncClient):
    _, h = await _register(client)
    for _ in range(4):
        r = await client.post(
            "/api/v1/execution/run",
            json={"language": "cobol", "code": "x"},
            headers=h,
        )
        assert r.status_code == 400
    r = await client.post(
        "/api/v1/execution/run", json={"language": "python", "code": "print(1)"}, headers=h
    )
    assert r.status_code == 200, r.text
    await _sse(client, h, f"/api/v1/execution/{r.json()['run_id']}/events")


# ── ad-hoc run endpoint ────────────────────────────────────────────


async def test_unknown_run_id_is_404_not_hang(client: AsyncClient):
    _, h = await _register(client)
    r = await client.get("/api/v1/execution/run_doesnotexist/events", headers=h)
    assert r.status_code == 404


async def test_run_stream_replays_queued_for_early_subscriber(client: AsyncClient):
    _, h = await _register(client)
    r = await client.post(
        "/api/v1/execution/run",
        json={"language": "python", "code": "print(1)", "stdin": "echo"},
        headers=h,
    )
    run_id = r.json()["run_id"]
    events = await _sse(client, h, f"/api/v1/execution/{run_id}/events")
    assert events[0]["kind"] == "queued"
    assert events[-1]["verdict"] == "finished"
    assert next(e for e in events if e["kind"] == "case_result")["stdout"] == "echo"


async def test_run_in_workspace_requires_editor(client: AsyncClient):
    _, owner_h = await _register(client, "owner")
    editor_email, editor_h = await _register(client, "editor")
    viewer_email, viewer_h = await _register(client, "viewer")
    _, outsider_h = await _register(client, "outsider")

    r = await client.post(
        "/api/v1/workspaces", json={"name": "run-ws", "language": "python"}, headers=owner_h
    )
    ws_id = r.json()["id"]
    for email, role in [(editor_email, "editor"), (viewer_email, "viewer")]:
        r = await client.post(
            f"/api/v1/workspaces/{ws_id}/members",
            json={"email": email, "role": role},
            headers=owner_h,
        )
        assert r.status_code == 201

    payload = {"language": "python", "code": "print(1)", "workspace_id": ws_id}
    for headers, expected in [
        (owner_h, 200),
        (editor_h, 200),
        (viewer_h, 403),
        (outsider_h, 403),
    ]:
        r = await client.post("/api/v1/execution/run", json=payload, headers=headers)
        assert r.status_code == expected, r.text
        if expected == 200:
            await _sse(client, headers, f"/api/v1/execution/{r.json()['run_id']}/events")

    r = await client.post(
        "/api/v1/execution/run", json={**payload, "workspace_id": "ws_nope"}, headers=owner_h
    )
    assert r.status_code == 404

"""Mock interviews (SOLVARY_INTERVIEWS_DESIGN.md §12): lifecycle, no-peek,
server clock + grace, advance policies, questions-format switching, derived
results, strict pacing, assist gating, RBAC. The clock is monkeypatched on
`interview_service.utcnow` — no sleeps."""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.services import interview_service
from tests.conftest import TEST_ADMIN_EMAIL, TEST_ADMIN_PASSWORD, ensure_two_sum

BASE = datetime(2026, 11, 4, 12, 0, tzinfo=UTC)


# ── helpers ────────────────────────────────────────────────────────


async def _admin(client: AsyncClient) -> dict:
    r = await client.post(
        "/api/auth/login", json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _register(client: AsyncClient, name: str = "cand") -> dict:
    r = await client.post(
        "/api/auth/register",
        json={
            "name": name,
            "email": f"{name}-{uuid.uuid4().hex[:8]}@test.dev",
            "password": "pw123456",
        },
    )
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _problem(client: AsyncClient, admin: dict, is_public: bool = False) -> dict:
    slug = f"iv-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/problems",
        json={
            "slug": slug,
            "title": f"Stage {slug}",
            "difficulty": "easy",
            "statement_md": f"Statement for {slug}",
            "starter_code": {"python": f"# starter {slug}\n", "javascript": "// js\n"},
            "is_public": is_public,
            "editorial_md": f"Editorial for {slug}",
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    problem = r.json()
    for ordinal, is_sample in ((1, True), (2, False)):
        r = await client.post(
            f"/api/v1/problems/{problem['id']}/testcases",
            json={
                "ordinal": ordinal,
                "stdin": f"{ordinal}\n",
                "expected_stdout": "ok\n",
                "is_sample": is_sample,
            },
            headers=admin,
        )
        assert r.status_code == 201, r.text
    return problem


async def _template(
    client: AsyncClient,
    admin: dict,
    problems: list[dict],
    fmt: str = "levels",
    duration_s: int = 600,
    budgets: list[int] | None = None,
    **extra,
) -> dict:
    r = await client.post(
        "/api/v1/interviews/templates",
        json={
            "slug": f"tpl-{uuid.uuid4().hex[:8]}",
            "title": "Test interview",
            "format": fmt,
            "duration_s": duration_s,
            "stages": [
                {
                    "problem_id": p["id"],
                    "title": f"Part {i + 1}",
                    "budget_s": budgets[i] if budgets else None,
                }
                for i, p in enumerate(problems)
            ],
            **extra,
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _start(client: AsyncClient, h: dict, template: dict) -> dict:
    r = await client.post(
        "/api/v1/interviews/sessions", json={"template_id": template["id"]}, headers=h
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _sse(client: AsyncClient, headers: dict, url: str) -> list[dict]:
    events = []
    async with client.stream("GET", url, headers=headers) as resp:
        assert resp.status_code == 200, await resp.aread()
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
                if events[-1].get("kind") in ("verdict", "error"):
                    break
    return events


async def _submit(
    client: AsyncClient, h: dict, session: dict, problem_id: str, code: str = "print('ok')"
):
    """POST an interview-tagged submission; drain the stream on success."""
    r = await client.post(
        "/api/v1/submissions",
        json={
            "problem_id": problem_id,
            "language": "python",
            "code": code,
            "workspace_id": session["workspace_id"],
            "interview_session_id": session["id"],
        },
        headers=h,
    )
    if r.status_code == 201:
        await _sse(client, h, f"/api/v1/submissions/{r.json()['id']}/events")
    return r


@pytest.fixture
def clock(monkeypatch):
    """Movable server clock: clock.now = ..."""

    class Clock:
        now = BASE

    monkeypatch.setattr(interview_service, "utcnow", lambda: Clock.now)
    return Clock


# ── tests ──────────────────────────────────────────────────────────


async def test_levels_lifecycle_no_peek_and_review(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(3)]
    tpl = await _template(client, admin, probs, budgets=[60, 120, 180])
    h = await _register(client)

    s = await _start(client, h, tpl)
    assert s["status"] == "active" and s["current_stage"] == 1 and s["unlocked_through"] == 1
    assert s["server_time"].startswith("2026-11-04T12:00")
    assert s["stages"][0]["problem"]["statement_md"] == f"Statement for {probs[0]['slug']}"
    assert s["stages"][0]["problem"]["sample_testcases"] == [
        {"ordinal": 1, "stdin": "1\n", "expected_stdout": "ok\n"}
    ]
    assert s["stages"][0]["file_id"]
    for locked in s["stages"][1:]:
        assert locked["locked"] and locked["problem"] is None and locked["file_id"] is None
        assert locked["editorial_md"] is None

    # No peeking: private stage problems are invisible outside the session
    r = await client.get(f"/api/v1/problems/{probs[1]['slug']}", headers=h)
    assert r.status_code == 404
    r = await client.get("/api/v1/problems", headers=h)
    assert probs[1]["id"] not in {p["id"] for p in r.json()["items"]}
    # ...and on the write path
    assert (await _submit(client, h, s, probs[1]["id"])).status_code == 403

    # The session workspace is hidden from the list and has a fixed file set
    r = await client.get("/api/v1/workspaces", headers=h)
    assert s["workspace_id"] not in {w["id"] for w in r.json()}
    r = await client.get(f"/api/v1/workspaces/{s['workspace_id']}", headers=h)
    assert r.status_code == 200 and r.json()["kind"] == "interview"
    r = await client.post(
        f"/api/v1/workspaces/{s['workspace_id']}/files", json={"path": "x.py"}, headers=h
    )
    assert r.status_code == 400
    files = (await client.get(f"/api/v1/workspaces/{s['workspace_id']}/files", headers=h)).json()
    assert [f["path"] for f in files] == ["main.py"]

    # Stage 1 accepted, then move on
    clock.now = BASE + timedelta(seconds=90)
    assert (await _submit(client, h, s, probs[0]["id"])).status_code == 201
    r = await client.get(f"/api/v1/interviews/sessions/{s['id']}/review", headers=h)
    assert r.status_code == 409  # still active
    r = await client.post(f"/api/v1/interviews/sessions/{s['id']}/advance", headers=h)
    assert r.status_code == 200, r.text
    s2 = r.json()
    assert s2["unlocked_through"] == 2 and s2["current_stage"] == 2
    assert s2["stages"][1]["problem"]["id"] == probs[1]["id"]
    assert s2["stages"][1]["file_id"] == s2["stages"][0]["file_id"]  # same buffer carries over
    assert s2["stages"][0]["result"]["best_verdict"] == "accepted"
    assert s2["stages"][0]["result"]["time_spent_s"] == 90
    assert [e["stage"] for e in s2["timeline"]] == [1, 2]
    # levels only move forward
    r = await client.post(
        f"/api/v1/interviews/sessions/{s['id']}/switch", json={"stage": 1}, headers=h
    )
    assert r.status_code == 409
    # the old part no longer accepts submissions
    assert (await _submit(client, h, s, probs[0]["id"])).status_code == 409

    clock.now = BASE + timedelta(seconds=400)
    r = await client.post(f"/api/v1/interviews/sessions/{s['id']}/finish", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "finished"
    assert r.json()["time_used_s"] == 400

    r = await client.get(f"/api/v1/interviews/sessions/{s['id']}/review", headers=h)
    assert r.status_code == 200, r.text
    review = r.json()
    assert all(st["problem"] is not None and not st["locked"] for st in review["stages"])
    assert review["stages"][2]["editorial_md"] == f"Editorial for {probs[2]['slug']}"
    assert review["score"] == {"passed": 2, "total": 6, "percent": 33}
    assert len(review["submissions"]) == 1
    assert review["submissions"][0]["interview_session_id"] == s["id"]
    assert "Part 2 took" in review["diagnosis"]  # 310 s on a 120 s budget
    assert "Part 3 never reached" in review["diagnosis"]

    # No further mutations once over
    for action in ("advance", "finish", "abandon"):
        r = await client.post(f"/api/v1/interviews/sessions/{s['id']}/{action}", headers=h)
        assert r.status_code == 409


async def test_server_clock_grace_and_lazy_expiry(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    tpl = await _template(client, admin, probs, duration_s=600)
    h = await _register(client)
    s = await _start(client, h, tpl)
    ends_at = BASE + timedelta(seconds=600)
    assert s["ends_at"].startswith("2026-11-04T12:10:00")

    clock.now = ends_at - timedelta(seconds=1)
    assert (await _submit(client, h, s, probs[0]["id"])).status_code == 201
    clock.now = ends_at + timedelta(seconds=2)  # inside the 3 s grace
    assert (await _submit(client, h, s, probs[0]["id"])).status_code == 201
    clock.now = ends_at + timedelta(seconds=5)
    r = await _submit(client, h, s, probs[0]["id"])
    assert r.status_code == 409 and "time is up" in r.json()["detail"].lower()

    # Lazy expiry on read; finished_at is the deadline, not the read time
    r = await client.get(f"/api/v1/interviews/sessions/{s['id']}", headers=h)
    assert r.json()["status"] == "expired"
    assert r.json()["finished_at"].startswith("2026-11-04T12:10:00")
    assert r.json()["time_used_s"] == 600
    r = await client.post(f"/api/v1/interviews/sessions/{s['id']}/advance", headers=h)
    assert r.status_code == 409
    r = await client.get(f"/api/v1/interviews/sessions/{s['id']}/review", headers=h)
    assert r.status_code == 200 and r.json()["diagnosis"]
    # ...and the user may start another
    assert (await client.get("/api/v1/interviews/sessions/active", headers=h)).json() is None
    s2 = await _start(client, h, tpl)
    assert s2["id"] != s["id"]


async def test_advance_policies(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    h = await _register(client)

    tpl = await _template(client, admin, probs, advance="on_accept")
    s = await _start(client, h, tpl)
    url = f"/api/v1/interviews/sessions/{s['id']}/advance"
    assert (await client.post(url, headers=h)).status_code == 409
    assert (await _submit(client, h, s, probs[0]["id"], "x __MOCK_WA__")).status_code == 201
    assert (await client.post(url, headers=h)).status_code == 409
    assert (await _submit(client, h, s, probs[0]["id"])).status_code == 201
    assert (await client.post(url, headers=h)).status_code == 200
    await client.post(f"/api/v1/interviews/sessions/{s['id']}/abandon", headers=h)

    tpl = await _template(client, admin, probs, advance="on_submit")
    s = await _start(client, h, tpl)
    url = f"/api/v1/interviews/sessions/{s['id']}/advance"
    assert (await client.post(url, headers=h)).status_code == 409
    assert (await _submit(client, h, s, probs[0]["id"], "x __MOCK_WA__")).status_code == 201
    assert (await client.post(url, headers=h)).status_code == 200
    assert (await client.post(url, headers=h)).status_code == 409  # last part


async def test_questions_format_switch_results_and_one_active_session(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    tpl = await _template(client, admin, probs, fmt="questions", budgets=[60, 60])
    h = await _register(client)

    s = await _start(client, h, tpl)
    assert s["unlocked_through"] == 2
    assert all(st["problem"] for st in s["stages"])
    assert s["stages"][0]["file_id"] != s["stages"][1]["file_id"]
    files = (await client.get(f"/api/v1/workspaces/{s['workspace_id']}/files", headers=h)).json()
    assert sorted(f["path"] for f in files) == ["q1.py", "q2.py"]

    # Only one interview at a time
    r = await client.post("/api/v1/interviews/sessions", json={"template_id": tpl["id"]}, headers=h)
    assert r.status_code == 409
    active = (await client.get("/api/v1/interviews/sessions/active", headers=h)).json()
    assert active["id"] == s["id"]

    # Best-of derivation: TLE (0/2) → accepted (2/2) → WA (1/2) ⇒ best stays 2/2
    for code in ("x __MOCK_TLE__", "x", "x __MOCK_WA__"):
        assert (await _submit(client, h, s, probs[0]["id"], code)).status_code == 201
    clock.now = BASE + timedelta(seconds=100)
    r = await client.post(
        f"/api/v1/interviews/sessions/{s['id']}/switch", json={"stage": 2}, headers=h
    )
    assert r.status_code == 200
    d = r.json()
    assert d["current_stage"] == 2 and [e["stage"] for e in d["timeline"]] == [1, 2]
    q1 = d["stages"][0]["result"]
    assert q1["submissions"] == 3 and q1["best_verdict"] == "accepted"
    assert (q1["best_passed"], q1["best_total"]) == (2, 2)
    assert d["stages"][1]["result"] == {
        "submissions": 0,
        "best_submission_id": None,
        "best_verdict": None,
        "best_passed": 0,
        "best_total": 2,
        "time_spent_s": 0,
    }
    assert d["score"] == {"passed": 2, "total": 4, "percent": 50}
    # questions never "advance"; bad stage numbers 404
    assert (
        await client.post(f"/api/v1/interviews/sessions/{s['id']}/advance", headers=h)
    ).status_code == 409
    r = await client.post(
        f"/api/v1/interviews/sessions/{s['id']}/switch", json={"stage": 3}, headers=h
    )
    assert r.status_code == 404

    r = await client.post(f"/api/v1/interviews/sessions/{s['id']}/abandon", headers=h)
    assert r.status_code == 200 and r.json()["status"] == "abandoned"
    assert (await client.get("/api/v1/interviews/sessions/active", headers=h)).json() is None
    listed = (await client.get("/api/v1/interviews/sessions", headers=h)).json()
    assert [x["id"] for x in listed["items"]] == [s["id"]]
    # Abandoned runs don't count as a template's last result
    tpls = (await client.get("/api/v1/interviews/templates", headers=h)).json()
    mine = next(t for t in tpls if t["id"] == tpl["id"])
    assert mine["last_result"] is None and [st["budget_s"] for st in mine["stages"]] == [60, 60]
    assert "problem" not in mine["stages"][0]


async def test_strict_pacing_auto_advances_levels(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(3)]
    tpl = await _template(client, admin, probs, budgets=[60, 60, 60], pacing="strict")
    h = await _register(client)
    s = await _start(client, h, tpl)
    assert s["stages"][0]["deadline_at"].startswith("2026-11-04T12:01:00")
    assert s["stages"][2]["deadline_at"].startswith("2026-11-04T12:03:00")

    clock.now = BASE + timedelta(seconds=61)
    d = (await client.get(f"/api/v1/interviews/sessions/{s['id']}", headers=h)).json()
    assert d["current_stage"] == 2 and d["unlocked_through"] == 2
    assert d["timeline"][1]["at"].startswith("2026-11-04T12:01:00")  # advanced AT the deadline
    assert (await _submit(client, h, s, probs[0]["id"])).status_code == 409  # part 1 is over

    clock.now = BASE + timedelta(seconds=130)
    d = (await client.get(f"/api/v1/interviews/sessions/{s['id']}", headers=h)).json()
    assert d["current_stage"] == 3
    assert (await _submit(client, h, s, probs[2]["id"])).status_code == 201


async def test_strict_pacing_locks_questions_after_their_deadline(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    tpl = await _template(client, admin, probs, fmt="questions", budgets=[60, 60], pacing="strict")
    h = await _register(client)
    s = await _start(client, h, tpl)
    clock.now = BASE + timedelta(seconds=70)
    r = await _submit(client, h, s, probs[0]["id"])
    assert r.status_code == 409 and "part is up" in r.json()["detail"]
    assert (await _submit(client, h, s, probs[1]["id"])).status_code == 201


async def test_assist_blocked_during_interview_allowed_on_review(client: AsyncClient, clock):
    admin = await _admin(client)
    public = await ensure_two_sum(client)
    private = await _problem(client, admin)
    tpl = await _template(client, admin, [public, private], fmt="questions")
    h = await _register(client)
    s = await _start(client, h, tpl)

    async def ask(body: dict) -> int:
        async with client.stream(
            "POST", "/api/v1/assist/explain", json={"question": "hint?", **body}, headers=h
        ) as resp:
            return resp.status_code

    assert await ask({"problem_id": public["id"]}) == 409  # in the interview → no help
    assert await ask({"problem_id": private["id"], "interview_session_id": s["id"]}) == 409
    assert await ask({"problem_id": private["id"]}) == 404

    await client.post(f"/api/v1/interviews/sessions/{s['id']}/finish", headers=h)
    assert await ask({"problem_id": private["id"], "interview_session_id": s["id"]}) == 200
    assert await ask({"problem_id": public["id"]}) == 200
    assert await ask({"problem_id": private["id"]}) == 404  # still private outside the session


async def test_session_rbac_and_unknowns(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin)]
    tpl = await _template(client, admin, probs)
    h = await _register(client)
    other = await _register(client, "other")
    s = await _start(client, h, tpl)

    url = f"/api/v1/interviews/sessions/{s['id']}"
    assert (await client.get(url, headers=other)).status_code == 403
    assert (await client.post(f"{url}/finish", headers=other)).status_code == 403
    assert (await client.get(url, headers=admin)).status_code == 200
    assert (
        await client.get("/api/v1/interviews/sessions/isess_nope", headers=h)
    ).status_code == 404
    assert (await client.get("/api/v1/interviews/templates/nope", headers=h)).status_code == 404
    r = await client.post("/api/v1/interviews/sessions", json={"template_id": "itpl_x"}, headers=h)
    assert r.status_code == 404
    # non-admins cannot author templates
    r = await client.post(
        "/api/v1/interviews/templates",
        json={
            "slug": "x",
            "title": "x",
            "format": "levels",
            "duration_s": 600,
            "stages": [{"problem_id": probs[0]["id"], "title": "p"}],
        },
        headers=h,
    )
    assert r.status_code == 403
    # another user's interview submission is refused
    r = await client.post(
        "/api/v1/submissions",
        json={
            "problem_id": probs[0]["id"],
            "language": "python",
            "code": "x",
            "interview_session_id": s["id"],
        },
        headers=other,
    )
    assert r.status_code == 403


async def test_custom_duration_scales_budgets_and_deadlines(client: AsyncClient, clock):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    # template: 90 min, budgets 30 + 60 min, strict
    tpl = await _template(
        client, admin, probs, duration_s=5400, budgets=[1800, 3600], pacing="strict"
    )
    h = await _register(client)
    r = await client.post(
        "/api/v1/interviews/sessions",
        json={"template_id": tpl["id"], "duration_s": 1800},  # run it in 30 min
        headers=h,
    )
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["duration_s"] == 1800 and s["template"]["duration_s"] == 5400
    assert s["ends_at"].startswith("2026-11-04T12:30:00")
    assert [st["budget_s"] for st in s["stages"]] == [600, 1200]  # scaled by 1/3
    assert s["stages"][0]["deadline_at"].startswith("2026-11-04T12:10:00")
    # the template listing still shows the template's own budgets
    tpls = (await client.get("/api/v1/interviews/templates", headers=h)).json()
    mine = next(t for t in tpls if t["id"] == tpl["id"])
    assert [st["budget_s"] for st in mine["stages"]] == [1800, 3600]
    # out-of-range durations are rejected
    r = await client.post(
        "/api/v1/interviews/sessions", json={"template_id": tpl["id"], "duration_s": 60}, headers=h
    )
    assert r.status_code == 422


def test_stage_times_and_deadlines_pure():
    from app.models.interview import InterviewStage, InterviewTemplate
    from app.services.interview_service import stage_deadlines, stage_times

    t0 = BASE
    timeline = [
        {"stage": 1, "at": t0.isoformat()},
        {"stage": 2, "at": (t0 + timedelta(seconds=100)).isoformat()},
        {"stage": 1, "at": (t0 + timedelta(seconds=150)).isoformat()},
    ]
    spent = stage_times(timeline, t0 + timedelta(seconds=200))
    assert spent == {1: 150.0, 2: 50.0}

    tpl = InterviewTemplate(
        id="t",
        slug="t",
        title="t",
        description_md="",
        format="levels",
        duration_s=600,
        pacing="strict",
    )
    stages = [
        InterviewStage(id="a", template_id="t", ordinal=1, problem_id="p1", title="1", budget_s=60),
        InterviewStage(
            id="b", template_id="t", ordinal=2, problem_id="p2", title="2", budget_s=None
        ),
        InterviewStage(id="c", template_id="t", ordinal=3, problem_id="p3", title="3", budget_s=60),
    ]
    d = stage_deadlines(tpl, stages, t0)
    assert d == {1: t0 + timedelta(seconds=60), 2: None, 3: None}
    tpl.pacing = "coached"
    assert stage_deadlines(tpl, stages, t0) == {1: None, 2: None, 3: None}

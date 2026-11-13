"""Interviewer agent (SOLVARY_INTERVIEWER_DESIGN.md §12): key storage, turn
validation, the SSE stream and the [silent] protocol, prompt assembly,
persistence into the transcript and the review payload, refusals, API
errors, the per-session lock, the limiter. Claude is the fake provider
(conftest sets INTERVIEWER_PROVIDER=fake); the clock is monkeypatched on
`interview_service.utcnow`."""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.secrets import InvalidToken, decrypt_secret, encrypt_secret
from app.models.interview import InterviewStage, InterviewTemplate
from app.models.interviewer import REFUSED, SILENT, InterviewerTurn
from app.models.problem import Problem
from app.models.testcase import TestCase as _Case
from app.models.user import User
from app.schemas.interviewer import JudgeFailure, JudgeSnapshot, ScreenContext
from app.schemas.interviews import StageResult
from app.services import interview_service, interviewer_service
from app.services.ai_keys import resolve_api_key
from app.services.claude_client import FakeClaudeClient, get_claude_client
from app.services.interviewer_prompt import (
    STATIC_SYSTEM,
    Truth,
    digest,
    render_screen,
    render_template_package,
    split_editorial,
)
from tests.test_interviews import _admin, _problem, _register, _start, _template

BASE = datetime(2026, 11, 12, 15, 0, tzinfo=UTC)
GOOD_KEY = "sk-ant-api03-" + "x" * 40 + "k3Qa"
BAD_KEY = "sk-ant-api03-" + "y" * 40 + "-bad"  # the fake rejects keys ending in -bad

SCREEN = {
    "stage": 1,
    "code": "def solve():\n    return 1\n",
    "code_changed_since_last_turn": True,
    "judge": None,
    "run": None,
    "visible_pane": "none",
    "seconds_since_last_edit": 4,
    "mic": "off",
}


@pytest.fixture
def clock(monkeypatch):
    class Clock:
        now = BASE

    monkeypatch.setattr(interview_service, "utcnow", lambda: Clock.now)
    return Clock


@pytest.fixture
def fake() -> FakeClaudeClient:
    client = get_claude_client()
    assert isinstance(client, FakeClaudeClient)
    client.reset()
    yield client
    client.reset()


async def _turn(
    client: AsyncClient, h: dict, session_id: str, body: dict
) -> tuple[int, list[dict]]:
    frames: list[dict] = []
    async with client.stream(
        "POST", f"/api/v1/interviews/sessions/{session_id}/interviewer/turns", json=body, headers=h
    ) as resp:
        if resp.status_code != 200:
            await resp.aread()
            return resp.status_code, [json.loads(resp.text)]
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                frames.append(json.loads(line[6:]))
    return 200, frames


def _typed(text: str, **screen) -> dict:
    return {"trigger": "typed", "utterance": text, "screen": {**SCREEN, **screen}}


async def _set_key(client: AsyncClient, h: dict, key: str = GOOD_KEY) -> dict:
    r = await client.put("/api/users/me/ai-key", json={"api_key": key}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


# ── API key ─────────────────────────────────────────────────────────


async def test_ai_key_lifecycle_never_returns_the_key(client: AsyncClient, fake):
    h = await _register(client, "keys")
    r = await client.get("/api/users/me/ai-key", headers=h)
    assert r.json() == {"configured": False, "last4": None, "source": "none"}

    r = await client.put(
        "/api/users/me/ai-key", json={"api_key": "not-a-key-at-all-really"}, headers=h
    )
    assert r.status_code == 422
    r = await client.post("/api/users/me/ai-key/test", headers=h)
    assert r.status_code == 402 and r.json()["error_code"] == "NO_API_KEY"

    status = await _set_key(client, h)
    assert status == {"configured": True, "last4": "k3Qa", "source": "user"}
    me = (await client.get("/api/users/me", headers=h)).json()
    assert GOOD_KEY not in json.dumps(me) and "k3Qa" not in json.dumps(me)

    # Encrypted at rest: the row holds a Fernet token, not the key
    from app.db.engine import async_session_factory
    from app.db.tables import UserRow

    async with async_session_factory() as s:
        row = (await s.execute(select(UserRow).where(UserRow.email == me["email"]))).scalar_one()
        assert row.anthropic_api_key_enc and GOOD_KEY not in row.anthropic_api_key_enc
        assert decrypt_secret(row.anthropic_api_key_enc) == GOOD_KEY
        assert row.anthropic_api_key_last4 == "k3Qa"

    r = await client.post("/api/users/me/ai-key/test", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True and r.json()["source"] == "user"
    assert fake.pings[-1] == (GOOD_KEY, "claude-sonnet-5-5")

    await _set_key(client, h, BAD_KEY)
    r = await client.post("/api/users/me/ai-key/test", headers=h)
    assert r.status_code == 400 and "401" in r.json()["detail"]

    r = await client.delete("/api/users/me/ai-key", headers=h)
    assert r.status_code == 200 and r.json()["configured"] is False


def test_secrets_round_trip_and_key_rotation():
    token = encrypt_secret("sk-ant-secret", secret_key="k1")
    assert token != "sk-ant-secret"
    assert decrypt_secret(token, secret_key="k1") == "sk-ant-secret"
    with pytest.raises(InvalidToken):
        decrypt_secret(token, secret_key="k2")

    from app.config import get_settings

    user = User(id="u", name="n", email="e@x", hashed_password="", avatar_url="")
    user.anthropic_api_key_enc = token  # written under a different SECRET_KEY
    key, source = resolve_api_key(user, get_settings())
    assert (key, source) == (None, "none")  # logged, not raised


# ── turn validation ─────────────────────────────────────────────────


async def test_turn_rejections(client: AsyncClient, clock, fake):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    tpl = await _template(client, admin, probs)
    h = await _register(client, "cand")
    s = await _start(client, h, tpl)
    url = f"/api/v1/interviews/sessions/{s['id']}/interviewer/turns"

    r = await client.post(url, json=_typed("hello"), headers=h)
    assert r.status_code == 402 and r.json()["error_code"] == "NO_API_KEY"

    await _set_key(client, h)
    other = await _register(client, "other")
    await _set_key(client, other)
    assert (await client.post(url, json=_typed("hi"), headers=other)).status_code == 403

    big = _typed("hi", code="x" * 70_000)
    assert (await client.post(url, json=big, headers=h)).status_code == 400
    assert (await client.post(url, json=_typed("hi", stage=9), headers=h)).status_code == 400
    r = await client.post(url, json={"trigger": "typed", "screen": SCREEN}, headers=h)
    assert r.status_code == 422  # utterance required
    r = await client.post(url, json={"trigger": "event", "screen": SCREEN}, headers=h)
    assert r.status_code == 422  # an event turn needs an event line

    # Lock held by an in-flight turn → 409
    lock = interviewer_service._lock_for(s["id"])
    await lock.acquire()
    try:
        r = await client.post(url, json=_typed("hi"), headers=h)
        assert r.status_code == 409 and "in progress" in r.json()["detail"]
    finally:
        lock.release()

    # Over the limiter → 429
    from app.core.rate_limit import interviewer_limiter

    me = (await client.get("/api/users/me", headers=h)).json()
    await interviewer_limiter.reset()  # the rejected POSTs above already counted
    for _ in range(40):
        await interviewer_limiter.check(me["id"])
    assert (await client.post(url, json=_typed("hi"), headers=h)).status_code == 429
    await interviewer_limiter.reset()

    # Finished session → 409
    await client.post(f"/api/v1/interviews/sessions/{s['id']}/finish", headers=h)
    assert (await client.post(url, json=_typed("hi"), headers=h)).status_code == 409
    assert fake.calls == []  # nothing reached Claude


# ── the stream ──────────────────────────────────────────────────────


async def test_stream_silent_protocol_history_and_review(client: AsyncClient, clock, fake):
    admin = await _admin(client)
    probs = [await _problem(client, admin) for _ in range(2)]
    tpl = await _template(client, admin, probs, budgets=[120, 180])
    h = await _register(client, "cand")
    await _set_key(client, h)
    s = await _start(client, h, tpl)
    sid = s["id"]

    # Opening turn: the model speaks
    clock.now = BASE + timedelta(seconds=30)
    fake.queue("Hi. Talk me through how you read part one.")
    status, frames = await _turn(
        client,
        h,
        sid,
        {"trigger": "opening", "events": ["The interview has started."], "screen": SCREEN},
    )
    assert status == 200
    text = "".join(f.get("content", "") for f in frames)
    assert text == "Hi. Talk me through how you read part one."
    done = frames[-1]
    assert done["done"] is True and done["spoke"] is True and done["refused"] is False
    assert done["usage"]["input_tokens"] == 100

    # The prompt: static system + cached template package, one user turn
    call = fake.calls[-1]
    assert call["api_key"] == GOOD_KEY and call["model"] == "claude-sonnet-5-5"
    assert call["effort"] == "low" and call["max_tokens"] == 1024
    assert call["system"][0]["text"] == STATIC_SYSTEM
    package = call["system"][1]["text"]
    assert call["system"][1]["cache_control"] == {"type": "ephemeral"}
    for p in probs:  # every part, locked ones included, with the editorial
        assert f"Statement for {p['slug']}" in package
        assert f"Editorial for {p['slug']}" in package
    assert "Sample 1 input" in package and "1 hidden" in package
    assert "2\n" not in package.split("Sample 1 input")[1].split("### ")[0]  # hidden stdin absent
    assert len(call["messages"]) == 1
    screen_text = call["messages"][0]["content"][0]["text"]
    assert "clock: 9:30 left" in screen_text  # the SERVER clock
    assert "0:30 spent of a 2:00 budget" in screen_text
    assert "def solve():" in screen_text
    assert "- The interview has started." in screen_text
    assert screen_text.rstrip().endswith("(no speech)")

    # Second turn: judge context, the model stays silent
    clock.now = BASE + timedelta(seconds=200)
    fake.queue(SILENT)
    judge = {
        "submission_id": "sub_x",
        "verdict": "wrong_answer",
        "passed": 1,
        "total": 2,
        "failures": [{"name": "Test 2", "detail": "expected ok got nope"}],
        "age_s": 3,
    }
    status, frames = await _turn(
        client,
        h,
        sid,
        {
            "trigger": "event",
            "events": ["Submission judged: wrong_answer 1/2."],
            "screen": {**SCREEN, "judge": judge, "code_changed_since_last_turn": False},
        },
    )
    assert status == 200
    assert [f for f in frames if "content" in f] == []  # nothing rendered
    assert frames[-1]["spoke"] is False and frames[-1]["done"] is True
    call = fake.calls[-1]
    assert len(call["messages"]) == 3  # earlier user + assistant, then this turn
    first = call["messages"][0]["content"]
    assert first.startswith("[stage 1 · 9:30 left · judge none · code 2 lines]")
    assert "def solve" not in first  # digest, never the old code
    assert call["messages"][1] == {
        "role": "assistant",
        "content": "Hi. Talk me through how you read part one.",
    }
    latest = call["messages"][2]["content"][0]["text"]
    assert "latest judge: wrong_answer 1/2 · 3s ago" in latest
    assert "- Test 2\n      expected ok got nope" in latest
    assert "OVER by 1:20" in latest  # 200 s on a 120 s budget
    assert "code changed since your last reply: no" in latest
    assert "def solve():" in latest  # the current code always rides on the newest turn

    # Typed question; the silent turn is replayed verbatim
    fake.queue("Why a dict and not a set here?")
    status, frames = await _turn(client, h, sid, _typed("I'm going to use a dict here"))
    assert status == 200 and frames[-1]["spoke"] is True
    call = fake.calls[-1]
    assert call["messages"][3] == {"role": "assistant", "content": SILENT}
    assert (
        call["messages"][4]["content"][0]["text"].rstrip().endswith("I'm going to use a dict here")
    )

    # Transcript: six rows in order, silent flagged, user turns carry digests
    r = await client.get(f"/api/v1/interviews/sessions/{sid}/interviewer/turns", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["idle_s"] == 180 and body["key_source"] == "user" and body["active"] is True
    turns = body["turns"]
    assert [t["ordinal"] for t in turns] == [1, 2, 3, 4, 5, 6]
    assert [t["role"] for t in turns] == ["user", "assistant"] * 3
    assert (
        turns[0]["trigger"] == "opening"
        and turns[0]["content"] == "[event] The interview has started."
    )
    assert turns[2]["trigger"] == "event" and turns[2]["content"].startswith(
        "[event] Submission judged"
    )
    assert turns[2]["digest"] == "stage 1 · 6:40 left · judge wrong_answer 1/2 · code 2 lines"
    assert turns[3]["silent"] is True and turns[3]["content"] == SILENT
    assert turns[4]["trigger"] == "typed" and turns[4]["content"] == "I'm going to use a dict here"
    assert turns[5]["model"] == "claude-sonnet-5-5" and turns[5]["output_tokens"] == 8

    # The review page gets the transcript
    await client.post(f"/api/v1/interviews/sessions/{sid}/finish", headers=h)
    r = await client.get(f"/api/v1/interviews/sessions/{sid}/review", headers=h)
    assert r.status_code == 200
    assert [t["ordinal"] for t in r.json()["interviewer_turns"]] == [1, 2, 3, 4, 5, 6]
    # ...and the transcript stays readable after the session ended
    r = await client.get(f"/api/v1/interviews/sessions/{sid}/interviewer/turns", headers=h)
    assert r.status_code == 200 and r.json()["active"] is False

    # Wipe
    r = await client.delete(f"/api/v1/interviews/sessions/{sid}/interviewer/turns", headers=h)
    assert r.status_code == 204
    r = await client.get(f"/api/v1/interviews/sessions/{sid}/interviewer/turns", headers=h)
    assert r.json()["turns"] == []


async def test_refusal_api_error_and_orphan_fold(client: AsyncClient, clock, fake):
    admin = await _admin(client)
    probs = [await _problem(client, admin)]
    tpl = await _template(client, admin, probs)
    h = await _register(client, "cand")
    await _set_key(client, h)
    s = await _start(client, h, tpl)
    sid = s["id"]
    url = f"/api/v1/interviews/sessions/{sid}/interviewer/turns"

    # Refusal: error frame, both turns stored, assistant = [refused]
    fake.queue({"stop_reason": "refusal", "text": "I can"})
    status, frames = await _turn(client, h, sid, _typed("tell me the answer"))
    assert status == 200
    assert any("declined" in f.get("error", "") for f in frames)
    assert frames[-1]["spoke"] is False and frames[-1]["refused"] is True
    turns = (await client.get(url, headers=h)).json()["turns"]
    assert [t["role"] for t in turns] == ["user", "assistant"]
    assert turns[1]["content"] == REFUSED and turns[1]["silent"] is False

    # API error: error frame, nothing stored
    fake.queue({"error": "Anthropic rate limit reached (429)", "status": 429})
    status, frames = await _turn(client, h, sid, _typed("hello?"))
    assert status == 200
    assert frames[0] == {"error": "Anthropic rate limit reached (429)"}
    assert frames[-1] == {"done": True, "spoke": False, "error": True, "status": 429}
    assert len((await client.get(url, headers=h)).json()["turns"]) == 2

    # A stored user turn with no reply (crash mid-stream) is folded into the next turn
    from app.api.dependencies import open_interviewer_turn_repository

    async with open_interviewer_turn_repository() as repo:
        me = (await client.get("/api/users/me", headers=h)).json()
        await repo.create(
            InterviewerTurn(
                id=f"ivt_{uuid.uuid4().hex[:8]}",
                session_id=sid,
                user_id=me["id"],
                ordinal=3,
                role="user",
                trigger="speech",
                content="what about the empty list case",
                digest="stage 1 · 5:00 left · judge none · code 2 lines",
            )
        )
    fake.queue("Good question — what should it return?")
    status, frames = await _turn(client, h, sid, _typed("still there?"))
    assert status == 200 and frames[-1]["spoke"] is True
    msgs = fake.calls[-1]["messages"]
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]  # no trailing orphan
    latest = msgs[-1]["content"][0]["text"]
    assert "earlier, unanswered" in latest and "empty list case" in latest
    turns = (await client.get(url, headers=h)).json()["turns"]
    assert [t["ordinal"] for t in turns] == [1, 2, 3, 4, 5]


async def test_pytest_stage_package_lists_harness_files(client: AsyncClient, clock, fake):
    admin = await _admin(client)
    suite = "import solution\n\ndef test_one():\n    assert solution.f() == 1\n"
    r = await client.post(
        "/api/v1/problems",
        json={
            "slug": f"ivp-{uuid.uuid4().hex[:8]}",
            "title": "Pytest stage",
            "difficulty": "easy",
            "statement_md": "Make f() return 1.",
            "starter_code": {"python": "def f():\n    pass\n"},
            "judge_mode": "pytest",
            "harness": {"module": "solution", "files": {"test_solution_p1.py": suite}},
            "is_public": False,
            "editorial_md": (
                "**Core pattern:** return 1\n\n### Interviewer notes\n\nWatch for off-by-one.\n\n"
                "### Reference solution\n\n```python\ndef f():\n    return 1\n```\n"
            ),
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    problem = r.json()
    r = await client.post(
        f"/api/v1/problems/{problem['id']}/testcases",
        json={
            "ordinal": 1,
            "stdin": "test_solution_p1.py::test_one",
            "expected_stdout": "PASS",
            "is_sample": True,
        },
        headers=admin,
    )
    assert r.status_code == 201, r.text
    tpl = await _template(client, admin, [problem])
    h = await _register(client, "cand")
    await _set_key(client, h)
    s = await _start(client, h, tpl)

    judge = {
        "submission_id": None,
        "verdict": "wrong_answer",
        "passed": 0,
        "total": 1,
        "failures": [{"name": "test_solution_p1.py::test_one", "detail": "assert None == 1"}],
        "age_s": 1,
    }
    status, frames = await _turn(client, h, s["id"], _typed("why does it fail", judge=judge))
    assert status == 200
    package = fake.calls[-1]["system"][1]["text"]
    assert "candidate's module: `solution.py`" in package
    assert "#### test_solution_p1.py" in package and "assert solution.f() == 1" in package
    assert "Watch for off-by-one." in package
    assert "def f():\n    return 1" in package  # reference solution (interviewer_knows_solutions)
    screen = fake.calls[-1]["messages"][-1]["content"][0]["text"]
    assert "provided tests for this part: test_solution_p1.py" in screen
    # the fake's default reply names the failing test
    assert "test_solution_p1.py::test_one" in "".join(f.get("content", "") for f in frames)


# ── prompt assembly (unit) ──────────────────────────────────────────


def test_split_editorial():
    md = (
        "**Core pattern:** heap\n\n### Interviewer notes\n\nWatch the tuple.\n\n"
        "### Reference solution\n\n```python\nimport heapq\n```\n"
    )
    assert split_editorial(md) == ("**Core pattern:** heap\n\nWatch the tuple.", "import heapq")
    assert split_editorial("Just prose.") == ("Just prose.", None)
    assert split_editorial(None) == (None, None)
    assert split_editorial("### Reference solution\n\nplain text") == (None, "plain text")


def _fixture_template():
    template = InterviewTemplate(
        id="itpl_1",
        slug="t",
        title="Heaps",
        description_md="Rules.",
        format="levels",
        duration_s=1800,
        advance="on_accept",
    )
    stages = [
        InterviewStage(
            id="istg_1",
            template_id="itpl_1",
            ordinal=1,
            problem_id="p1",
            title="Part 1",
            budget_s=600,
        ),
        InterviewStage(
            id="istg_2",
            template_id="itpl_1",
            ordinal=2,
            problem_id="p2",
            title="Part 2",
            budget_s=None,
        ),
    ]
    problems = {
        "p1": Problem(
            id="p1",
            slug="p1",
            title="One",
            difficulty="easy",
            statement_md="Do one.",
            editorial_md="### Reference solution\n\n```python\nprint(1)\n```\n",
        ),
        "p2": Problem(id="p2", slug="p2", title="Two", difficulty="easy", statement_md="Do two."),
    }
    cases = {
        "p1": [
            _Case(
                id="c1",
                problem_id="p1",
                ordinal=1,
                stdin="1\n",
                expected_stdout="1\n",
                is_sample=True,
            ),
            _Case(id="c2", problem_id="p1", ordinal=2, stdin="SECRET\n", expected_stdout="2\n"),
        ],
        "p2": [],
    }
    return template, stages, problems, cases


def test_render_template_package_solutions_toggle_and_hidden_cases():
    template, stages, problems, cases = _fixture_template()
    with_ref = render_template_package(template, stages, problems, cases, include_solutions=True)
    assert "## Part 1: Part 1 (10 min budget)" in with_ref
    assert "## Part 2: Part 2 (no budget)" in with_ref
    assert "Do one." in with_ref and "Do two." in with_ref
    assert "print(1)" in with_ref
    assert "SECRET" not in with_ref and "1 hidden" in with_ref
    without = render_template_package(template, stages, problems, cases, include_solutions=False)
    assert "print(1)" not in without and "Do two." in without
    assert with_ref == render_template_package(
        template, stages, problems, cases, True
    )  # deterministic


def test_render_screen_and_digest():
    truth = Truth(
        template_title="Heaps",
        format="levels",
        status="active",
        language="python",
        remaining_s=845,
        current_stage=2,
        unlocked_through=2,
        stage_count=3,
        stage_title="Part 2",
        stage_budget_s=600,
        stage_elapsed_s=650,
        results={
            1: StageResult(
                submissions=1,
                best_submission_id="s",
                best_verdict="accepted",
                best_passed=7,
                best_total=7,
                time_spent_s=490,
            ),
            2: StageResult(
                submissions=2,
                best_submission_id="s2",
                best_verdict="wrong_answer",
                best_passed=5,
                best_total=7,
                time_spent_s=650,
            ),
            3: StageResult(
                submissions=0,
                best_submission_id=None,
                best_verdict=None,
                best_passed=0,
                best_total=4,
                time_spent_s=0,
            ),
        },
        stage_titles={1: "Part 1", 2: "Part 2", 3: "Part 3"},
        harness_files={"test_x_p2.py": 1200},
    )
    screen = ScreenContext(
        stage=2,
        code="import heapq\n\nheap = []\n",
        judge=JudgeSnapshot(
            submission_id="s2",
            verdict="wrong_answer",
            passed=5,
            total=7,
            age_s=12,
            failures=[JudgeFailure(name="test_x_p2.py::test_lazy", detail="StopIteration")],
        ),
        visible_pane="judge",
        seconds_since_last_edit=40,
        mic="open",
    )
    text = render_screen(truth, screen, ["Submission judged: wrong_answer 5/7."], "um so")
    assert text.startswith("<screen>\n") and "</screen>\n<events>\n- Submission judged" in text
    assert "clock: 14:05 left" in text
    assert 'current part: 2 "Part 2" · 10:50 spent of a 10:00 budget — OVER by 0:50' in text
    assert (
        "P1 accepted 7/7 (1 submission, 8:10 spent); "
        "P2 wrong_answer 5/7 (2 submissions, 10:50 spent); P3 locked"
    ) in text
    assert "latest judge: wrong_answer 5/7 · 12s ago" in text
    assert "  - test_x_p2.py::test_lazy\n      StopIteration" in text
    assert "latest run: none" in text
    assert "visible pane: judge" in text and "mic: open" in text
    assert "code (3 lines, python):\n```python\nimport heapq\n\nheap = []\n```" in text
    assert text.rstrip().endswith("um so")
    assert digest(truth, screen) == "stage 2 · 14:05 left · judge wrong_answer 5/7 · code 3 lines"

    empty = render_screen(truth, ScreenContext(stage=2, code="   \n"), [], None)
    assert "code: (editor is empty)" in empty and empty.rstrip().endswith("(no speech)")
    assert "<events>" not in empty

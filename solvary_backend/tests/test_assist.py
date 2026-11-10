"""AI assistant endpoint: SSE stream shape, prompt assembly, validation,
rate limiting. Runs against the mock LLM provider (no network)."""

import json
import uuid

from httpx import AsyncClient

from app.core.rate_limit import TooManyRequestsException, assist_limiter
from app.schemas.assist import AssistRequest
from app.services.assist_service import AssistService
from app.services.llm_service import ChatMessage, LLMChunk, MockLLMService
from tests.conftest import ensure_two_sum


async def _register(client: AsyncClient) -> dict:
    r = await client.post(
        "/api/auth/register",
        json={
            "name": "asker",
            "email": f"ask-{uuid.uuid4().hex[:8]}@test.dev",
            "password": "pw123456",
        },
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _stream(client: AsyncClient, headers: dict, body: dict) -> tuple[int, list[dict]]:
    frames: list[dict] = []
    async with client.stream(
        "POST", "/api/v1/assist/explain", json=body, headers=headers
    ) as resp:
        if resp.status_code != 200:
            return resp.status_code, []
        async for line in resp.aiter_lines():
            if line.startswith("data: "):
                frames.append(json.loads(line[6:]))
    return 200, frames


async def test_explain_streams_chunks_then_done(client: AsyncClient):
    h = await _register(client)
    problem = await ensure_two_sum(client)
    status, frames = await _stream(
        client,
        h,
        {
            "problem_id": problem["id"],
            "code": "print('hi')",
            "language": "python",
            "verdict": "wrong_answer on test 2",
            "question": "Why does my code fail?",
        },
    )
    assert status == 200
    assert frames[-1] == {"done": True}
    text = "".join(f.get("content", "") for f in frames[:-1])
    assert len(text) > 50
    assert all("content" in f for f in frames[:-1])


async def test_explain_requires_auth_and_question(client: AsyncClient):
    r = await client.post("/api/v1/assist/explain", json={"question": "hi"})
    assert r.status_code == 401
    h = await _register(client)
    r = await client.post("/api/v1/assist/explain", json={"question": ""}, headers=h)
    assert r.status_code == 422


async def test_explain_unknown_problem_404(client: AsyncClient):
    h = await _register(client)
    status, _ = await _stream(client, h, {"problem_id": "prob_nope", "question": "?"})
    assert status == 404


async def test_explain_rate_limited_per_user(client: AsyncClient):
    h = await _register(client)
    me = (await client.get("/api/users/me", headers=h)).json()["id"]
    # Burn the window directly (20/min) rather than streaming 20 replies
    for _ in range(20):
        await assist_limiter.check(me)
    status, _ = await _stream(client, h, {"question": "one more?"})
    assert status == 429
    try:
        await assist_limiter.check(me)
    except TooManyRequestsException:
        pass


async def test_prompt_includes_statement_samples_code_and_never_hidden_cases(
    client: AsyncClient,
):
    """Prompt assembly (unit): statement + sample tests + code + verdict +
    question, hidden-case stdin absent."""
    from app.config import get_settings
    from app.db.engine import async_session_factory
    from app.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository
    from app.repositories.sqlalchemy_testcase_repository import SQLAlchemyTestCaseRepository

    problem = await ensure_two_sum(client)
    async with async_session_factory() as session:
        service = AssistService(
            SQLAlchemyProblemRepository(session),
            SQLAlchemyTestCaseRepository(session),
            MockLLMService(token_delay_s=0),
            get_settings(),
        )
        messages = await service.build_messages(
            AssistRequest(
                problem_id=problem["id"],
                code="print(0, 1)",
                language="python",
                verdict="wrong_answer on test 3",
                question="hint?",
            )
        )
    assert messages[0].role == "system"
    user = messages[1].content
    assert "Two Sum" in user
    assert "4 9\n2 7 11 15" in user  # sample 1 stdin
    assert "5 0\n-3 4 3 90 1" not in user  # hidden case 4 stdin
    assert "```python\nprint(0, 1)\n```" in user
    assert "wrong_answer on test 3" in user
    assert user.rstrip().endswith("hint?")


async def test_mock_llm_ends_with_done():
    chunks = [
        c async for c in MockLLMService(token_delay_s=0).stream_response(
            [ChatMessage(role="user", content="x")]
        )
    ]
    assert chunks[-1] == LLMChunk(content="", done=True)
    assert all(not c.done for c in chunks[:-1])

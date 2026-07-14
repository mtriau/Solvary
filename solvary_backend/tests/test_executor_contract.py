"""
Executor contract tests (design §9): the same invariant suite runs against
every BaseExecutor implementation.

  - MockExecutor: always
  - PistonExecutor: only when a Piston engine is reachable (integration —
    run with `pytest -m piston`; skipped automatically otherwise)

Invariants (§6.1): no `verdict` events (worker owns the verdict); case_result
events carry ordinal + stdout for finished cases; resource failures surface
as case statuses; compile failures surface as a single `error` event.
"""

import httpx
import pytest

from app.config import get_settings
from app.services.execution.base import BaseExecutor, ExecCase, ExecJob
from app.services.execution.mock_executor import MockExecutor
from app.services.execution.piston_executor import PistonExecutor


def _piston_available() -> bool:
    try:
        response = httpx.get(
            f"{get_settings().piston_base_url}/api/v2/runtimes", timeout=2.0
        )
        return response.status_code == 200 and len(response.json()) > 0
    except httpx.HTTPError:
        return False


PISTON_AVAILABLE = _piston_available()

EXECUTORS: list = [pytest.param(MockExecutor(case_delay_s=0), id="mock")]
if PISTON_AVAILABLE:
    EXECUTORS.append(
        pytest.param(
            PistonExecutor(get_settings().piston_base_url),
            id="piston",
            marks=pytest.mark.piston,
        )
    )


def _judge_job(code: str, cases: list[ExecCase] | None = None, language: str = "python") -> ExecJob:
    return ExecJob(
        id="sub_test",
        user_id="user_test",
        language=language,
        code=code,
        mode="judge",
        cases=cases
        or [
            ExecCase(ordinal=1, stdin="1 2\n", expected_stdout="3\n", is_sample=True),
            ExecCase(ordinal=2, stdin="10 20\n", expected_stdout="30\n"),
        ],
        time_limit_s=4.0,
        memory_kb=256_000,
    )


async def _collect(executor: BaseExecutor, job: ExecJob):
    return [e async for e in executor.execute(job)]


# Real code used against Piston; MockExecutor ignores it (echoes expected)
ADD_TWO_PY = "import sys\nprint(sum(map(int, sys.stdin.read().split())))\n"


@pytest.mark.parametrize("executor", EXECUTORS)
async def test_no_verdict_events(executor: BaseExecutor):
    events = await _collect(executor, _judge_job(ADD_TWO_PY))
    assert all(e.kind != "verdict" for e in events), "executors must never emit verdicts"


@pytest.mark.parametrize("executor", EXECUTORS)
async def test_case_results_have_ordinals_and_stdout(executor: BaseExecutor):
    events = await _collect(executor, _judge_job(ADD_TWO_PY))
    case_results = [e for e in events if e.kind == "case_result"]
    assert {e.ordinal for e in case_results} == {1, 2}
    for event in case_results:
        assert event.status == "finished"
        assert event.stdout is not None
        assert event.runtime_ms is not None


@pytest.mark.parametrize("executor", EXECUTORS)
async def test_run_mode_single_case(executor: BaseExecutor):
    job = ExecJob(
        id="run_test",
        user_id="user_test",
        language="python",
        code="print(input())",
        mode="run",
        stdin="echo me\n",
        time_limit_s=4.0,
        memory_kb=256_000,
    )
    events = await _collect(executor, job)
    results = [e for e in events if e.kind == "case_result"]
    assert len(results) == 1
    assert results[0].stdout is not None


# ── Piston-only: real code, real sandbox behavior ─────────────────


@pytest.mark.piston
@pytest.mark.skipif(not PISTON_AVAILABLE, reason="Piston not reachable")
class TestPistonReal:
    @pytest.fixture
    def executor(self) -> PistonExecutor:
        return PistonExecutor(get_settings().piston_base_url)

    async def test_correct_python_output(self, executor):
        events = await _collect(executor, _judge_job(ADD_TWO_PY))
        results = {e.ordinal: e for e in events if e.kind == "case_result"}
        assert results[1].stdout == "3\n"
        assert results[2].stdout == "30\n"

    async def test_javascript_runtime(self, executor):
        code = (
            "const nums = require('fs').readFileSync(0,'utf8').trim().split(/\\s+/).map(Number);\n"
            "console.log(nums.reduce((a,b)=>a+b,0));\n"
        )
        events = await _collect(executor, _judge_job(code, language="javascript"))
        results = {e.ordinal: e for e in events if e.kind == "case_result"}
        assert results[1].stdout == "3\n"

    async def test_infinite_loop_is_tle(self, executor):
        job = _judge_job("while True: pass\n")
        job.time_limit_s = 2.0
        events = await _collect(executor, job)
        first = next(e for e in events if e.kind == "case_result")
        assert first.status == "tle"

    async def test_exception_is_runtime_error(self, executor):
        events = await _collect(executor, _judge_job("raise ValueError('boom')\n"))
        first = next(e for e in events if e.kind == "case_result")
        assert first.status == "runtime_error"

    async def test_sandbox_blocks_network(self, executor):
        code = (
            "import urllib.request\n"
            "urllib.request.urlopen('http://example.com', timeout=3)\n"
            "print('escaped')\n"
        )
        events = await _collect(executor, _judge_job(code))
        first = next(e for e in events if e.kind == "case_result")
        assert first.status in ("runtime_error", "tle")
        assert (first.stdout or "") == ""

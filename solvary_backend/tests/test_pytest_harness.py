"""
pytest judge mode: the sandbox runner, its output parser, and the Piston
executor's fan-out — exercised against a *fake Piston* that really runs the
file set with the local interpreter (so the runner and shim are tested for
real, without Docker).
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
import pytest

from app.services.execution import pytest_harness as ph
from app.services.execution.base import ExecCase, ExecJob
from app.services.execution.piston_executor import PistonExecutor

CONTENT = Path(__file__).resolve().parent.parent / "content" / "perplexity_prep"
TODO = CONTENT / "todo_tracker"

SUITE = '''
import pytest
from calc import add, Counter

def test_add():
    assert add(1, 2) == 3

def test_add_negative():
    assert add(-1, -2) == -3

def test_raises_on_str():
    with pytest.raises(TypeError):
        add("a", 1)

def test_raises_with_value():
    with pytest.raises(ValueError) as exc:
        raise ValueError("boom [1, 2]")
    assert "[1, 2]" in str(exc.value)

def test_approx():
    assert [0.1 + 0.2, 1.0] == pytest.approx([0.3, 1.0])

class TestCounter:
    def test_starts_at_zero(self):
        assert Counter().n == 0

    def test_incr(self):
        c = Counter(); c.incr(); c.incr()
        assert c.n == 2

def helper():  # not a test
    pass
'''

GOOD = '''
def add(a, b):
    if isinstance(a, str) or isinstance(b, str):
        raise TypeError("numbers only")
    return a + b

class Counter:
    def __init__(self):
        self.n = 0
    def incr(self):
        self.n += 1
'''

BUGGY = '''
def add(a, b):
    print("debug:", a, b)
    if isinstance(a, str):
        return a  # should have raised
    return a - b

class Counter:
    def __init__(self):
        self.n = 1
    def incr(self):
        self.n += 1
'''


def _fake_piston(run_status: str | None = None, cut_after: int | None = None):
    """Piston /api/v2/execute that writes the files to a temp dir and runs them."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        with tempfile.TemporaryDirectory() as tmp:
            for f in payload["files"]:
                (Path(tmp) / f["name"]).write_text(f["content"], encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-I", "main.py"],
                cwd=tmp,
                input=payload["stdin"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        stdout = proc.stdout
        if cut_after is not None:  # simulate the run dying mid-suite
            parts = stdout.split(ph.RECORD_MARK)
            stdout = ph.RECORD_MARK.join(parts[: cut_after + 1])
        run = {
            "stdout": stdout,
            "stderr": proc.stderr,
            "code": proc.returncode,
            "signal": None,
            "cpu_time": 12,
            "memory": 10_000_000,
        }
        if run_status:
            run["status"] = run_status
            run["signal"] = "SIGKILL"
        return httpx.Response(200, json={"run": run, "language": "python", "version": "3"})

    return httpx.MockTransport(handler)


def _job(code: str, files: dict[str, str], module: str = "calc") -> ExecJob:
    ids = [tid for name, src in files.items() for tid in ph.collect_test_ids(name, src)]
    return ExecJob(
        id="sub_x",
        user_id="u",
        language="python",
        code=code,
        mode="judge",
        harness={"module": module, "files": files},
        cases=[
            ExecCase(ordinal=i, stdin=tid, expected_stdout="PASS\n", is_sample=True)
            for i, tid in enumerate(ids, 1)
        ],
        time_limit_s=15.0,
    )


async def _results(executor: PistonExecutor, job: ExecJob) -> list:
    return [e async for e in executor.execute(job)]


# ── collection & parsing ───────────────────────────────────────────


def test_collect_test_ids_in_definition_order_including_classes():
    ids = ph.collect_test_ids("test_calc.py", SUITE)
    assert ids == [
        "test_calc.py::test_add",
        "test_calc.py::test_add_negative",
        "test_calc.py::test_raises_on_str",
        "test_calc.py::test_raises_with_value",
        "test_calc.py::test_approx",
        "test_calc.py::TestCounter::test_starts_at_zero",
        "test_calc.py::TestCounter::test_incr",
    ]


def test_parse_output_tolerates_truncated_tail():
    out = (
        f"{ph.RECORD_MARK}t.py::a\nPASS 3\n{ph.RECORD_END}\n"
        f"{ph.RECORD_MARK}t.py::b\nFAIL 7\nAssertionError: nope\nmore\n{ph.RECORD_END}\n"
        f"{ph.RECORD_MARK}t.py::c\nPASS 1\n"  # died before END
    )
    parsed = ph.parse_output(out)
    assert parsed.compile_error is None
    assert parsed.records["t.py::a"].status == "PASS"
    assert parsed.records["t.py::b"].detail == "AssertionError: nope\nmore"
    assert parsed.records["t.py::b"].runtime_ms == 7
    assert "t.py::c" not in parsed.records


def test_parse_output_compile_error():
    parsed = ph.parse_output(f"{ph.COMPILE_ERROR_MARK}\nSyntaxError: bad\n")
    assert parsed.compile_error == "SyntaxError: bad"


# ── end to end through the executor ────────────────────────────────


@pytest.mark.asyncio
async def test_good_solution_passes_every_test():
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    events = await _results(executor, _job(GOOD, {"test_calc.py": SUITE}))
    results = [e for e in events if e.kind == "case_result"]
    assert len(results) == 7
    assert all(e.status == "finished" and e.stdout == "PASS\n" for e in results)
    assert all(e.runtime_ms is not None for e in results)
    assert not [e for e in events if e.kind == "verdict"]


@pytest.mark.asyncio
async def test_buggy_solution_reports_named_failures_with_assertion_and_captured_output():
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    job = _job(BUGGY, {"test_calc.py": SUITE})
    events = await _results(executor, job)
    by_id = {
        job.cases[e.ordinal - 1].stdin: e for e in events if e.kind == "case_result"
    }
    assert by_id["test_calc.py::test_add"].stdout.startswith("FAIL\n")
    assert "assert" in by_id["test_calc.py::test_add"].stdout
    assert "debug: 1 2" in by_id["test_calc.py::test_add"].stdout  # captured print
    raised = by_id["test_calc.py::test_raises_on_str"].stdout
    assert raised.startswith("FAIL\n") and "DID NOT RAISE TypeError" in raised
    assert "pytest.py" not in raised and "Temp" not in raised  # only suite/module frames
    assert by_id["test_calc.py::test_raises_with_value"].stdout == "PASS\n"
    assert by_id["test_calc.py::test_approx"].stdout == "PASS\n"
    assert by_id["test_calc.py::TestCounter::test_starts_at_zero"].stdout.startswith("FAIL\n")
    assert by_id["test_calc.py::TestCounter::test_incr"].stdout.startswith("FAIL\n")


@pytest.mark.asyncio
async def test_syntax_error_is_a_single_compile_error_event():
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    events = await _results(executor, _job("def add(a, b:\n    return", {"test_calc.py": SUITE}))
    assert [e.kind for e in events] == ["compiling", "error"]
    assert events[1].status == "compile_error"
    assert "SyntaxError" in (events[1].message or "")


@pytest.mark.asyncio
async def test_missing_symbol_fails_every_test_of_that_file_with_the_import_error():
    suite2 = "from calc import multiply\n\ndef test_mul():\n    assert multiply(2, 3) == 6\n"
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    job = _job(GOOD, {"test_calc.py": SUITE, "test_calc_p2.py": suite2})
    events = await _results(executor, job)
    results = [e for e in events if e.kind == "case_result"]
    assert len(results) == 8
    assert results[-1].stdout.startswith("FAIL\ncould not import the test module")
    assert "multiply" in results[-1].stdout
    assert all(e.stdout == "PASS\n" for e in results[:-1])


@pytest.mark.asyncio
async def test_run_timeout_marks_unreported_tests_as_tle():
    executor = PistonExecutor(
        "http://piston.test", transport=_fake_piston(run_status="TO", cut_after=3)
    )
    events = await _results(executor, _job(GOOD, {"test_calc.py": SUITE}))
    results = [e for e in events if e.kind == "case_result"]
    assert [e.status for e in results[:3]] == ["finished"] * 3
    assert all(e.status == "tle" for e in results[3:])


@pytest.mark.asyncio
async def test_crash_marks_unreported_tests_as_runtime_error():
    executor = PistonExecutor(
        "http://piston.test", transport=_fake_piston(run_status="XX", cut_after=2)
    )
    events = await _results(executor, _job(GOOD, {"test_calc.py": SUITE}))
    results = [e for e in events if e.kind == "case_result"]
    assert [e.status for e in results] == ["finished"] * 2 + ["runtime_error"] * 5


# ── the real seeded content: reference solutions must be green ────────


@pytest.mark.skipif(not TODO.exists(), reason="perplexity content not present")
@pytest.mark.asyncio
async def test_todo_tracker_reference_passes_all_four_parts_and_stub_fails():
    files = {
        f"test_todo_tracker_p{n}.py": (TODO / f"test_todo_tracker_p{n}.py").read_text(
            encoding="utf-8"
        )
        for n in range(1, 5)
    }
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())

    reference = (TODO / "reference.py").read_text(encoding="utf-8")
    job = _job(reference, files, module="todo_tracker")
    assert len(job.cases) == 97
    results = [
        e for e in await _results(executor, job) if e.kind == "case_result"
    ]
    failed = [job.cases[e.ordinal - 1].stdin for e in results if e.stdout != "PASS\n"]
    assert failed == []

    stub = (TODO / "todo_tracker.py").read_text(encoding="utf-8")
    results = [
        e
        for e in await _results(executor, _job(stub, files, module="todo_tracker"))
        if e.kind == "case_result"
    ]
    assert all(e.status == "finished" and e.stdout.startswith("FAIL\n") for e in results)
    assert "NotImplementedError" in results[0].stdout


# ── ad-hoc Run over a provided suite (RunRequest.problem_id) ───────────


def _run_job(code: str, files: dict[str, str], stdin: str, module: str = "calc") -> ExecJob:
    return ExecJob(
        id="run_x",
        user_id="u",
        language="python",
        code=code,
        mode="run",
        harness={"module": module, "files": files},
        stdin=stdin,
        time_limit_s=15.0,
    )


async def _run_transcript(code: str, stdin: str):
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    events = await _results(executor, _run_job(code, {"test_calc.py": SUITE}, stdin))
    return events[-1]


@pytest.mark.asyncio
async def test_run_mode_runs_only_the_listed_tests_and_shows_prints():
    result = await _run_transcript(
        BUGGY, "test_calc.py::test_add\ntest_calc.py::test_raises_with_value\n"
    )
    assert result.kind == "case_result" and result.status == "finished"
    out = result.stdout
    assert "FAIL  test_calc.py::test_add" in out
    assert "debug: 1 2" in out  # what the module printed, under the failing test
    assert "PASS  test_calc.py::test_raises_with_value" in out
    assert out.rstrip().endswith("1 passed, 1 failed")
    assert "test_add_negative" not in out  # unrequested tests did not run


@pytest.mark.asyncio
async def test_run_mode_blank_stdin_runs_whole_suite_and_keeps_output_of_passing_tests():
    chatty = GOOD.replace("    return a + b", '    print("adding", a, b)\n    return a + b')
    result = await _run_transcript(chatty, "")
    out = result.stdout
    assert out.rstrip().endswith("7 passed, 0 failed")
    assert "adding 1 2" in out  # judging hides prints on PASS; Run shows them


@pytest.mark.asyncio
async def test_run_mode_unknown_test_id_is_reported_not_crashed():
    result = await _run_transcript(GOOD, "test_calc.py::test_nope\n")
    assert result.status == "finished"
    assert "FAIL  test_calc.py::test_nope" in result.stdout
    assert "not found in the provided suite" in result.stdout


@pytest.mark.asyncio
async def test_run_mode_syntax_error_is_a_compile_error():
    result = await _run_transcript("def add(:\n", "")
    assert result.kind == "error" and result.status == "compile_error"
    assert "SyntaxError" in (result.message or "")


def test_format_run_output_marks_missing_records():
    parsed = ph.HarnessOutput(
        compile_error=None,
        records={"t.py::a": ph.HarnessRecord(status="PASS", runtime_ms=3, detail="")},
    )
    out = ph.format_run_output(["t.py::a", "t.py::b"], parsed)
    assert out.splitlines()[0] == "PASS  t.py::a  (3 ms)"
    assert out.splitlines()[1].startswith("?     t.py::b  (no result")
    assert out.rstrip().endswith("1 passed, 1 failed")

"""
Python prelude: common stdlib names work without an import in plain scripts
(stdin/stdout problems, ad-hoc Run) and in pytest-mode modules, tracebacks
still point at the user's own file and line, and the API describes the list.
Runs against the fake Piston (the real local interpreter).
"""

import builtins
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.services.execution import python_prelude
from app.services.execution.base import ExecCase, ExecJob
from app.services.execution.piston_executor import PistonExecutor
from tests.test_pytest_harness import _fake_piston, _job, _results

pytestmark = pytest.mark.asyncio


def _script(code: str, stdin: str = "", mode: str = "run") -> ExecJob:
    cases = [] if mode == "run" else [ExecCase(ordinal=1, stdin=stdin, expected_stdout="")]
    return ExecJob(
        id="run_prelude",
        user_id="u",
        language="python",
        code=code,
        mode=mode,
        stdin=stdin,
        cases=cases,
        time_limit_s=10.0,
    )


async def _run(code: str, stdin: str = "", mode: str = "run"):
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    events = await _results(executor, _script(code, stdin, mode))
    (result,) = [e for e in events if e.kind == "case_result"]
    return result


async def test_script_uses_prelude_names_without_imports():
    code = (
        "words = input().split()\n"
        "c = Counter(words)\n"
        "d = defaultdict(list)\n"
        "for w in words:\n"
        "    d[len(w)].append(w)\n"
        "h = []\n"
        "for w in words:\n"
        "    heappush(h, w)\n"
        "nums: List[int] = [gcd(12, 18), math.lcm(4, 6), floor(2.7), inf > 10**9]\n"
        "print(c.most_common(1)[0], sorted(d), heappop(h), nums, deque([1]).popleft())\n"
        "print(''.join(ascii_lowercase[:3]), list(pairwise([1, 2, 3])), "
        "reduce(lambda a, b: a + b, [1, 2, 3]))\n"
    )
    result = await _run(code, stdin="b a b\n")
    assert result.status == "finished", result
    assert result.stdout.splitlines() == [
        "('b', 2) [1] a [6, 12, 2, True] 1",
        "abc [(1, 2), (2, 3)] 6",
    ]


async def test_script_still_runs_as_main_and_reads_all_stdin():
    code = (
        "import sys\n"
        "if __name__ == '__main__':\n"
        "    data = sys.stdin.read().split()\n"
        "    print(sum(map(int, data)), __file__)\n"
    )
    result = await _run(code, stdin="1 2\n3\n", mode="judge")
    assert result.status == "finished"
    assert result.stdout == "6 solution.py\n"


async def test_script_traceback_points_at_user_file_and_line():
    code = "x = 1\ny = 2\nraise ValueError('boom %d' % (x + y))\n"
    result = await _run(code)
    assert result.status == "runtime_error"
    assert 'File "solution.py", line 3' in result.message
    assert "ValueError: boom 3" in result.message
    assert "main.py" not in result.message and "solvary_prelude" not in result.message


async def test_script_syntax_error_names_user_file():
    result = await _run("def f(:\n    pass\n")
    assert result.status == "runtime_error"
    assert 'File "solution.py", line 1' in result.message
    assert "SyntaxError" in result.message


async def test_script_exit_code_and_user_imports_still_work():
    assert (await _run("import sys\nsys.exit(3)\n")).status == "runtime_error"
    result = await _run("from collections import Counter\nprint(Counter('aab')['a'])\n")
    assert result.status == "finished" and result.stdout == "2\n"


async def test_prelude_does_not_shadow_user_or_real_builtins():
    code = (
        "count = 0\n"
        "for _ in range(3):\n"
        "    count += 1\n"
        "def product(a, b):\n"
        "    return a * b\n"
        "print(count, product(2, 3), sum([1, 2]), type(count).__name__)\n"
    )
    result = await _run(code)
    assert result.status == "finished" and result.stdout == "3 6 3 int\n"


async def test_pytest_module_uses_prelude_names():
    module = (
        "def top(words):\n"
        "    return Counter(words).most_common(1)[0][0]\n"
        "def grouped(nums):\n"
        "    d = defaultdict(list)\n"
        "    for n in nums:\n"
        "        d[n % 2].append(n)\n"
        "    return dict(d)\n"
    )
    suite = (
        "from m import top, grouped\n\n"
        "def test_top():\n    assert top('a b a'.split()) == 'a'\n\n"
        "def test_grouped():\n    assert grouped([1, 2, 3]) == {1: [1, 3], 0: [2]}\n"
    )
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    results = [
        e
        for e in await _results(executor, _job(module, {"test_m.py": suite}, module="m"))
        if e.kind == "case_result"
    ]
    assert [r.stdout for r in results] == ["PASS\n", "PASS\n"], results


def test_prelude_installs_into_builtins_in_a_fresh_interpreter():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / python_prelude.PRELUDE_FILENAME).write_text(
            python_prelude.prelude_source(), encoding="utf-8"
        )
        probe = (
            "import sys; sys.path.insert(0, sys.argv[1])\n"
            "import builtins, collections, solvary_prelude\n"
            "before = builtins.sum\n"
            "solvary_prelude.install(); solvary_prelude.install()\n"
            "assert builtins.Counter is collections.Counter\n"
            "assert builtins.collections is collections\n"
            "assert builtins.sum is before\n"
            "print('ok')\n"
        )
        proc = subprocess.run(
            [sys.executable, "-I", "-c", probe, tmp],
            cwd=tmp,
            capture_output=True,
            text=True,
            timeout=30,
        )
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "ok"
    assert not hasattr(builtins, "Counter")  # the test process itself is untouched


async def test_prelude_endpoint_lists_modules_and_names(client: AsyncClient):
    resp = await client.get("/api/v1/execution/prelude")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["language"] == "python"
    assert body["modules"][:2] == ["collections", "itertools"]
    assert "Counter" in body["names"]["collections"]
    assert body["names"]["re"] == []

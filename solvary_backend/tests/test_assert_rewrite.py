"""
Assertion rewriting in the pytest-mode runner: a failing `assert` reports the
values it compared (Expected / Actual for ==, both operands otherwise, the
value for a bare assert) plus a short diff, each operand evaluated once, with
the traceback still on the original line. Runs through the fake Piston.
"""

import pytest

from app.services.execution.piston_executor import PistonExecutor
from tests.test_pytest_harness import _fake_piston, _job, _results

pytestmark = pytest.mark.asyncio

MODULE = """
calls = []

def word_lengths(words):
    calls.append(1)
    return {w: len(w) + 1 for w in words}

def top(nums):
    return sorted(nums)[:2]

def shout(s):
    return s.upper() + "?"

def tags():
    return {"a", "c"}
"""

SUITE = """
import pytest
from m import word_lengths, top, shout, tags, calls

def test_dict():
    assert word_lengths(["hi", "yo"]) == {"hi": 2, "yo": 2}

def test_list():
    assert top([5, 3, 1]) == [1, 3, 5]

def test_str():
    assert shout("abc") == "ABC!"

def test_set():
    assert tags() == {"a", "b"}

def test_other_op():
    assert len(top([1, 2, 3])) > 5

def test_bare():
    assert top([]), "expected something"

def test_not():
    assert not top([1])

def test_chained():
    assert 1 < len(top([9, 8])) < 2

def test_approx():
    assert [0.1 + 0.2] == pytest.approx([0.5])

def test_type_mismatch():
    assert top([1]) == (1,)

def test_evaluated_once():
    before = len(calls)
    assert word_lengths(["xy"]) == {"xy": 2}
    assert len(calls) == before + 1  # never reached, but the record shows one call

def test_passes():
    assert word_lengths(["a"]) == {"a": 2}
    assert 1 < 2 < 3
    assert not []
"""


async def _details() -> dict[str, str]:
    executor = PistonExecutor("http://piston.test", transport=_fake_piston())
    job = _job(MODULE, {"test_m.py": SUITE}, module="m")
    events = [e for e in await _results(executor, job) if e.kind == "case_result"]
    by_id = {}
    for case, event in zip(job.cases, events):
        by_id[case.stdin.split("::")[1]] = event.stdout or ""
    return by_id


async def test_failure_details_show_expected_and_actual():
    d = await _details()

    assert d["test_passes"] == "PASS\n"

    dict_fail = d["test_dict"]
    assert 'File "test_m.py", line 6, in test_dict' in dict_fail
    assert "Expected: {'hi': 2, 'yo': 2}" in dict_fail
    assert "Actual:   {'hi': 3, 'yo': 3}" in dict_fail
    assert "'hi': expected 2, got 3" in dict_fail

    list_fail = d["test_list"]
    assert "Expected: [1, 3, 5]" in list_fail and "Actual:   [1, 3]" in list_fail
    assert "length: expected 3, got 2" in list_fail
    assert "missing from index 2: [5]" in list_fail

    str_fail = d["test_str"]
    assert "Expected: 'ABC!'" in str_fail and "Actual:   'ABC?'" in str_fail
    assert "first difference at index 3: expected '!', got '?'" in str_fail

    set_fail = d["test_set"]
    assert "missing: ['b']" in set_fail and "unexpected: ['c']" in set_fail

    other = d["test_other_op"]
    assert "Left:  2" in other and "Right: 5" in other and "(> is False)" in other

    bare = d["test_bare"]
    assert "expected something" in bare and "Value: []" in bare

    assert "Value: [1]" in d["test_not"]

    chained = d["test_chained"]
    assert "Operand 1: 1" in chained and "Operand 2: 2" in chained and "Operand 3: 2" in chained

    approx = d["test_approx"]
    assert "Expected: approx([0.5])" in approx and "Differences" not in approx

    assert "type: expected tuple, got list" in d["test_type_mismatch"]

    once = d["test_evaluated_once"]
    assert "Expected: {'xy': 2}" in once and "Actual:   {'xy': 3}" in once

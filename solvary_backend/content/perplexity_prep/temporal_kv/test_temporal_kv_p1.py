# Provided tests for Part 1: set / get as-of. Run with: pytest temporal_kv -q
# Each test name says which sentence of PROBLEM.md it checks.

import time

from temporal_kv import TemporalKV


def test_spec_example():
    kv = TemporalKV()
    kv.set("a", "1", 1)
    kv.set("a", "2", 5)
    kv.set("b", "x", 5)
    assert kv.get("a", 0) is None
    assert kv.get("a", 1) == "1"
    assert kv.get("a", 3) == "1"
    assert kv.get("a", 5) == "2"
    assert kv.get("a", 100) == "2"
    assert kv.get("b", 4) is None
    assert kv.get("zzz", 5) is None


def test_get_before_first_set_is_none():
    kv = TemporalKV()
    kv.set("a", "v", 10)
    assert kv.get("a", 9) is None
    assert kv.get("a", 0) is None


def test_get_exactly_at_set_timestamp_returns_that_value():
    kv = TemporalKV()
    kv.set("a", "v1", 3)
    kv.set("a", "v2", 7)
    assert kv.get("a", 3) == "v1"
    assert kv.get("a", 7) == "v2"


def test_get_between_sets_returns_earlier_value():
    kv = TemporalKV()
    kv.set("a", "v1", 3)
    kv.set("a", "v2", 7)
    assert kv.get("a", 4) == "v1"
    assert kv.get("a", 6) == "v1"


def test_get_after_last_set_returns_latest_value():
    kv = TemporalKV()
    kv.set("a", "v1", 3)
    kv.set("a", "v2", 7)
    assert kv.get("a", 8) == "v2"
    assert kv.get("a", 10**9) == "v2"


def test_same_timestamp_later_set_wins():
    kv = TemporalKV()
    kv.set("a", "first", 5)
    kv.set("a", "second", 5)
    assert kv.get("a", 5) == "second"
    assert kv.get("a", 6) == "second"


def test_same_timestamp_three_sets_last_call_wins():
    kv = TemporalKV()
    kv.set("a", "1", 1)
    kv.set("a", "3", 3)
    kv.set("a", "4", 3)
    kv.set("a", "5", 3)
    assert kv.get("a", 3) == "5"
    assert kv.get("a", 2) == "1"


def test_unknown_key_is_none():
    kv = TemporalKV()
    kv.set("a", "v", 1)
    assert kv.get("nope", 1) is None
    assert kv.get("nope", 0) is None


def test_get_on_unknown_key_does_not_create_an_entry():
    kv = TemporalKV()
    assert kv.get("ghost", 5) is None
    assert kv.get("ghost", 5) is None
    assert kv.get("ghost", 0) is None
    kv.set("ghost", "v", 10)
    assert kv.get("ghost", 9) is None
    assert kv.get("ghost", 10) == "v"


def test_keys_are_independent():
    kv = TemporalKV()
    kv.set("a", "va", 1)
    kv.set("b", "vb", 2)
    kv.set("a", "va2", 3)
    assert kv.get("a", 2) == "va"
    assert kv.get("b", 1) is None
    assert kv.get("b", 2) == "vb"
    assert kv.get("b", 100) == "vb"
    assert kv.get("a", 100) == "va2"


def test_get_may_be_called_in_any_timestamp_order():
    kv = TemporalKV()
    for t in range(1, 6):
        kv.set("a", f"v{t}", t * 10)
    assert kv.get("a", 50) == "v5"
    assert kv.get("a", 10) == "v1"
    assert kv.get("a", 35) == "v3"
    assert kv.get("a", 5) is None
    assert kv.get("a", 20) == "v2"


def test_empty_string_value_is_a_real_value_not_none():
    kv = TemporalKV()
    kv.set("a", "", 1)
    assert kv.get("a", 1) == ""
    assert kv.get("a", 5) == ""


def test_timestamp_zero_is_valid():
    kv = TemporalKV()
    kv.set("a", "zero", 0)
    assert kv.get("a", 0) == "zero"
    assert kv.get("a", 1) == "zero"


def test_later_set_keeps_earlier_history_readable():
    kv = TemporalKV()
    kv.set("a", "old", 1)
    kv.set("a", "new", 2)
    assert kv.get("a", 1) == "old"
    assert kv.get("a", 2) == "new"


def test_get_is_logarithmic_100k_sets_and_gets_under_two_seconds():
    kv = TemporalKV()
    n = 100_000
    start = time.perf_counter()
    for t in range(n):
        kv.set("k", f"v{t}", t)
    for t in range(n):
        assert kv.get("k", t) == f"v{t}"
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"100K sets + 100K gets took {elapsed:.2f}s; get must be O(log n)"

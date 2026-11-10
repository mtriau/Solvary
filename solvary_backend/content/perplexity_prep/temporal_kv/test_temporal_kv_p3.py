# Provided tests for Part 3: restore(ts). Run with: pytest temporal_kv -q

import time

from temporal_kv import TemporalKV


def test_restore_discards_mutations_strictly_after_ts():
    kv = TemporalKV()
    kv.set("a", "v1", 1)
    kv.set("a", "v2", 5)
    kv.restore(3)
    assert kv.get("a", 10) == "v1"
    assert kv.get("a", 5) == "v1"


def test_restore_keeps_mutation_at_equal_timestamp():
    kv = TemporalKV()
    kv.set("a", "v1", 1)
    kv.set("a", "v2", 5)
    kv.restore(5)
    assert kv.get("a", 10) == "v2"
    assert kv.get_range("a", 0, 10) == [(1, "v1"), (5, "v2")]


def test_restore_before_anything_happened_is_a_noop():
    kv = TemporalKV()
    kv.restore(0)
    kv.restore(100)
    kv.set("a", "v", 1)
    assert kv.get("a", 1) == "v"
    assert kv.get_range("a", 0, 10) == [(1, "v")]


def test_restore_to_zero_makes_every_key_read_none():
    kv = TemporalKV()
    kv.set("a", "va", 1)
    kv.set("b", "vb", 2)
    kv.delete("a", 3)
    kv.set("c", "vc", 4)
    kv.restore(0)
    for key in ("a", "b", "c"):
        assert kv.get(key, 10**9) is None
        assert kv.get_range(key, 0, 10**9) == []


def test_restore_with_ts_at_or_beyond_latest_mutation_changes_nothing():
    kv = TemporalKV()
    kv.set("a", "v1", 1)
    kv.set("a", "v2", 5)
    kv.restore(5)
    kv.restore(1000)
    assert kv.get_range("a", 0, 10) == [(1, "v1"), (5, "v2")]


def test_restore_then_set_at_the_same_ts_is_legal():
    kv = TemporalKV()
    kv.set("a", "v1", 1)
    kv.set("a", "v2", 5)
    kv.restore(3)
    kv.set("a", "v3", 3)
    assert kv.get("a", 3) == "v3"
    assert kv.get("a", 2) == "v1"
    assert kv.get("a", 10) == "v3"
    assert kv.get_range("a", 0, 10) == [(1, "v1"), (3, "v3")]


def test_restore_then_writes_resume_from_ts():
    kv = TemporalKV()
    kv.set("a", "v1", 1)
    kv.set("a", "v2", 8)
    kv.set("b", "w1", 9)
    kv.restore(4)
    kv.set("b", "w2", 4)
    kv.set("a", "v4", 6)
    assert kv.get("a", 7) == "v4"
    assert kv.get("a", 8) == "v4"
    assert kv.get("b", 9) == "w2"
    assert kv.get_range("a", 0, 100) == [(1, "v1"), (6, "v4")]
    assert kv.get_range("b", 0, 100) == [(4, "w2")]


def test_restore_then_get_range_reflects_only_survivors():
    kv = TemporalKV()
    kv.set("a", "v", 1)
    kv.delete("a", 5)
    kv.set("a", "w", 9)
    kv.restore(6)
    assert kv.get_range("a", 0, 100) == [(1, "v"), (5, None)]
    assert kv.get("a", 100) is None


def test_restore_discards_deletes_as_well_as_sets():
    kv = TemporalKV()
    kv.set("a", "v", 1)
    kv.delete("a", 5)
    kv.restore(3)
    assert kv.get("a", 5) == "v"
    assert kv.get("a", 100) == "v"
    assert kv.get_range("a", 0, 100) == [(1, "v")]


def test_restore_applies_across_all_keys():
    kv = TemporalKV()
    kv.set("a", "a1", 1)
    kv.set("b", "b1", 2)
    kv.set("a", "a2", 3)
    kv.set("c", "c1", 4)
    kv.set("b", "b2", 5)
    kv.restore(3)
    assert kv.get("a", 100) == "a2"
    assert kv.get("b", 100) == "b1"
    assert kv.get("c", 100) is None


def test_restore_leaves_keys_with_no_later_mutations_untouched():
    kv = TemporalKV()
    kv.set("old", "o", 1)
    kv.set("new", "n", 10)
    kv.restore(5)
    assert kv.get("old", 100) == "o"
    assert kv.get_range("old", 0, 100) == [(1, "o")]
    assert kv.get("new", 100) is None


def test_two_restores_in_a_row():
    kv = TemporalKV()
    for t in range(1, 10):
        kv.set("a", f"v{t}", t)
    kv.restore(7)
    assert kv.get("a", 100) == "v7"
    kv.restore(3)
    assert kv.get("a", 100) == "v3"
    assert kv.get_range("a", 0, 100) == [(1, "v1"), (2, "v2"), (3, "v3")]


def test_restore_keeps_earlier_history_of_the_same_key():
    kv = TemporalKV()
    for t in (1, 2, 3, 4):
        kv.set("a", f"v{t}", t)
    kv.restore(2)
    assert kv.get("a", 1) == "v1"
    assert kv.get("a", 2) == "v2"
    assert kv.get("a", 3) == "v2"
    assert kv.get("a", 0) is None


def test_key_emptied_by_restore_answers_get_none_without_error():
    kv = TemporalKV()
    kv.set("solo", "v", 7)
    kv.restore(6)
    assert kv.get("solo", 7) is None
    assert kv.get("solo", 100) is None


def test_key_emptied_by_restore_answers_get_range_empty_without_error():
    kv = TemporalKV()
    kv.set("solo", "v", 7)
    kv.restore(6)
    assert kv.get_range("solo", 0, 100) == []
    kv.set("solo", "again", 6)
    assert kv.get_range("solo", 0, 100) == [(6, "again")]


def test_restore_same_timestamp_set_and_delete_both_survive_or_both_go():
    kv = TemporalKV()
    kv.set("a", "v", 5)
    kv.delete("a", 5)
    kv.restore(5)
    assert kv.get_range("a", 0, 10) == [(5, "v"), (5, None)]
    kv.restore(4)
    assert kv.get_range("a", 0, 10) == []


def test_restore_to_midpoint_100k_sets_over_1k_keys_under_two_seconds():
    kv = TemporalKV()
    n = 100_000
    keys = [f"k{i}" for i in range(1_000)]
    for t in range(n):
        kv.set(keys[t % 1_000], f"v{t}", t)
    start = time.perf_counter()
    kv.restore(n // 2)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"restore over 100K mutations took {elapsed:.2f}s"
    # k0 wrote at t = 50000, which equals the midpoint, so it is kept
    assert kv.get("k0", n) == "v50000"
    # k500 wrote at t = 49500 (kept) and t = 50500 (discarded)
    assert kv.get("k500", n) == "v49500"
    assert kv.get_range("k1", n // 2 + 1, n) == []

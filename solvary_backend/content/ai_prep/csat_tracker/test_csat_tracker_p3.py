# Provided tests for Part 3: percentiles and distribution.

import time

import csat_tracker
import pytest


def make(window=1000):
    return csat_tracker.CSATTracker(window)


def fill(t, scores, start=1):
    for i, s in enumerate(scores):
        t.record(f"c{start + i}", s, start + i)


def test_percentile_none_when_empty():
    assert make().get_percentile(10, 50) is None


def test_median_of_four_is_second_smallest():
    t = make()
    fill(t, [5, 1, 4, 2])  # sorted 1 2 4 5
    assert t.get_percentile(4, 50) == 2


def test_median_of_odd_count():
    t = make()
    fill(t, [5, 1, 3, 3, 2])  # sorted 1 2 3 3 5
    assert t.get_percentile(5, 50) == 3


def test_p100_is_max_and_p0_is_min():
    t = make()
    fill(t, [3, 5, 1, 4])
    assert t.get_percentile(4, 100) == 5
    assert t.get_percentile(4, 0) == 1


def test_nearest_rank_cases():
    t = make()
    fill(t, [1, 1, 2, 3, 3, 3, 4, 5, 5, 5])  # n = 10
    assert t.get_percentile(10, 10) == 1  # ceil(1.0) - 1 = 0
    assert t.get_percentile(10, 11) == 1  # ceil(1.1) - 1 = 1
    assert t.get_percentile(10, 30) == 2  # index 2
    assert t.get_percentile(10, 70) == 4  # index 6
    assert t.get_percentile(10, 90) == 5  # index 8


def test_percentile_accepts_float_p():
    t = make()
    fill(t, [1, 2, 3, 4])
    assert t.get_percentile(4, 99.9) == 4
    assert t.get_percentile(4, 25.0) == 1
    assert t.get_percentile(4, 25.1) == 2


def test_percentile_ignores_expired_scores():
    t = make(5)
    t.record("a", 1, 10)
    t.record("b", 5, 14)
    assert t.get_percentile(14, 0) == 1
    assert t.get_percentile(16, 0) == 5
    assert t.get_percentile(30, 50) is None


def test_percentile_reflects_updates():
    t = make()
    fill(t, [1, 1, 1, 5])
    assert t.get_percentile(4, 50) == 1
    assert t.update("c1", 5, 5) is True
    assert t.update("c2", 5, 5) is True
    assert t.get_percentile(5, 50) == 5  # sorted 1 5 5 5, rank 2 -> index 1
    assert t.get_percentile(5, 25) == 1
    assert t.get_percentile(5, 26) == 5


def test_percentile_out_of_range_raises():
    t = make()
    t.record("a", 3, 1)
    for bad in (-1, 100.5, 101):
        with pytest.raises(ValueError):
            t.get_percentile(1, bad)


def test_distribution_empty_has_all_five_keys():
    assert make().get_distribution(5) == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


def test_distribution_counts_active_scores():
    t = make()
    fill(t, [5, 5, 3, 1, 5])
    assert t.get_distribution(5) == {1: 1, 2: 0, 3: 1, 4: 0, 5: 3}


def test_distribution_after_expiry_and_update():
    t = make(5)
    t.record("a", 1, 10)
    t.record("b", 2, 12)
    t.record("c", 2, 14)
    assert t.update("b", 4, 15) is True
    assert t.get_distribution(15) == {1: 1, 2: 1, 3: 0, 4: 1, 5: 0}
    assert t.get_distribution(16) == {1: 0, 2: 1, 3: 0, 4: 1, 5: 0}
    assert t.update("a", 5, 16) is False
    assert t.get_distribution(20) == {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}


def test_performance_200k_records_with_interleaved_queries():
    t = make(1000)
    start = time.perf_counter()
    for i in range(1, 200_001):
        t.record(f"c{i}", i % 5 + 1, i)
        if i % 2 == 0:
            t.get_average(i)
            t.get_percentile(i, 50)
        if i % 10 == 0:
            t.update(f"c{i - 3}", 5, i)
            t.get_distribution(i)
    elapsed = time.perf_counter() - start
    assert sum(t.get_distribution(200_000).values()) == 1001
    assert elapsed < 2.0, f"too slow: {elapsed:.2f}s (O(n) scan per query?)"

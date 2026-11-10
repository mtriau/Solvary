# Provided tests for Part 3: gaps and max concurrency.

from debug_view import gaps, max_concurrent

SPEC = [(0, 5, "a"), (3, 8, "b"), (10, 12, "c"), (12, 13, "d"), (15, 16, "e")]


def test_spec_examples():
    assert gaps(SPEC) == [(8, 10), (13, 15)]
    assert max_concurrent(SPEC) == 2
    assert max_concurrent([(0, 5, "a"), (5, 8, "b")]) == 1


def test_gaps_empty_and_single():
    assert gaps([]) == []
    assert gaps([(0, 5, "a")]) == []


def test_gaps_none_when_fully_covered():
    assert gaps([(0, 5, "a"), (5, 8, "b"), (2, 6, "c")]) == []


def test_gaps_unsorted_input():
    assert gaps([(15, 16, "e"), (0, 5, "a"), (10, 12, "c")]) == [(5, 10), (12, 15)]


def test_gaps_contained_segment_does_not_create_a_gap():
    assert gaps([(0, 10, "a"), (2, 3, "b"), (12, 13, "c")]) == [(10, 12)]


def test_gaps_are_maximal_windows():
    assert gaps([(0, 1, "a"), (5, 6, "b"), (5, 7, "c"), (9, 10, "d")]) == [(1, 5), (7, 9)]


def test_max_concurrent_empty():
    assert max_concurrent([]) == 0


def test_max_concurrent_nested():
    assert max_concurrent([(0, 10, "a"), (2, 8, "b"), (4, 6, "c")]) == 3


def test_max_concurrent_half_open_boundaries():
    assert max_concurrent([(0, 5, "a"), (5, 10, "b"), (5, 6, "c")]) == 2
    assert max_concurrent([(0, 5, "a"), (4, 5, "b"), (5, 6, "c")]) == 2


def test_max_concurrent_identical_segments():
    assert max_concurrent([(1, 2, "a")] * 7) == 7


def test_large_input_is_fast():
    segs = [(i, i + 50, "x") for i in range(200_000)]
    assert max_concurrent(segs) == 50
    assert gaps(segs) == []

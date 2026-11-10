# Provided tests for Part 2: (any_overlap, any_gap).

from debug_view import coverage_flags


def test_spec_examples():
    assert coverage_flags([(0, 5, "a"), (5, 8, "b")]) == (False, False)
    assert coverage_flags([(0, 5, "a"), (3, 8, "b")]) == (True, False)
    assert coverage_flags([(0, 5, "a"), (6, 8, "b")]) == (False, True)
    assert coverage_flags([(0, 5, "a"), (3, 8, "b"), (9, 10, "c")]) == (True, True)


def test_fewer_than_two_segments():
    assert coverage_flags([]) == (False, False)
    assert coverage_flags([(0, 5, "a")]) == (False, False)


def test_unsorted_input():
    assert coverage_flags([(6, 8, "b"), (0, 5, "a")]) == (False, True)
    assert coverage_flags([(3, 8, "b"), (0, 5, "a")]) == (True, False)


def test_contained_interval_is_an_overlap_not_a_gap():
    assert coverage_flags([(0, 10, "a"), (2, 3, "b"), (4, 5, "c")]) == (True, False)


def test_gap_after_a_contained_interval():
    # the furthest end is 10, so the gap is (10, 12) and not (3, 4)
    assert coverage_flags([(0, 10, "a"), (2, 3, "b"), (12, 14, "c")]) == (True, True)


def test_identical_segments_overlap():
    assert coverage_flags([(1, 2, "a"), (1, 2, "b")]) == (True, False)


def test_result_is_a_two_tuple_of_bools():
    out = coverage_flags([(0, 1, "a"), (1, 2, "b")])
    assert out == (False, False)
    assert isinstance(out, tuple) and len(out) == 2
    assert out[0] is False and out[1] is False


def test_large_input_is_fast():
    segs = [(i * 3, i * 3 + 2, "x") for i in range(200_000)]
    assert coverage_flags(segs) == (False, True)
    segs2 = [(i, i + 2, "x") for i in range(200_000)]
    assert coverage_flags(segs2) == (True, False)

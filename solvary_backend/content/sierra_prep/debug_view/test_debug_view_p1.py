# Provided tests for Part 1: merge overlapping half-open log segments.

from debug_view import merge_segments


def test_spec_example_one():
    assert merge_segments([(0, 5, "A"), (3, 10, "B"), (12, 15, "C")]) == [(0, 10, "A B"), (12, 15, "C")]


def test_spec_example_touching_does_not_merge():
    assert merge_segments([(1, 4, "X"), (4, 6, "Y"), (5, 8, "Z")]) == [(1, 4, "X"), (4, 8, "Y Z")]


def test_empty():
    assert merge_segments([]) == []


def test_single():
    assert merge_segments([(3, 7, "only")]) == [(3, 7, "only")]


def test_unsorted_input_is_sorted_first():
    assert merge_segments([(10, 12, "c"), (0, 3, "a"), (2, 5, "b")]) == [(0, 5, "a b"), (10, 12, "c")]


def test_contained_segment_keeps_the_outer_end():
    assert merge_segments([(0, 10, "outer"), (2, 4, "inner")]) == [(0, 10, "outer inner")]


def test_chain_of_overlaps_merges_into_one():
    segs = [(0, 2, "a"), (1, 3, "b"), (2, 4, "c"), (3, 5, "d")]
    assert merge_segments(segs) == [(0, 5, "a b c d")]


def test_same_start_smaller_end_first():
    assert merge_segments([(0, 9, "long"), (0, 2, "short")]) == [(0, 9, "short long")]


def test_same_start_and_end_keep_input_order():
    assert merge_segments([(0, 2, "second"), (0, 2, "first")]) == [(0, 2, "second first")]
    assert merge_segments([(0, 2, "first"), (0, 2, "second")]) == [(0, 2, "first second")]


def test_non_overlapping_stay_separate_and_sorted():
    assert merge_segments([(5, 6, "b"), (0, 1, "a"), (9, 10, "c")]) == [(0, 1, "a"), (5, 6, "b"), (9, 10, "c")]


def test_input_is_not_mutated():
    segs = [(3, 10, "B"), (0, 5, "A")]
    snapshot = list(segs)
    merge_segments(segs)
    assert segs == snapshot


def test_large_input_is_fast():
    segs = [(i * 2, i * 2 + 3, f"t{i}") for i in range(100_000)]
    out = merge_segments(segs)
    assert len(out) == 1
    assert out[0][0] == 0 and out[0][1] == 99_999 * 2 + 3
    assert out[0][2].startswith("t0 t1 t2 ") and out[0][2].endswith(" t99999")

# Provided tests for Part 2: one limit per row.

import homepage_dedup as hd
import pytest

ROWS = [["A", "B", "A", "C"], ["B", "D", "B", "E"], ["A", "F", "A"]]


def test_fastprep_style_example_with_per_row_limits():
    assert hd.dedupe_rows(ROWS, [2, 2, 1]) == [["A", "B", "C"], ["D", "E"], ["F"]]


def test_a_plain_int_still_means_the_same_limit_everywhere():
    assert hd.dedupe_rows(ROWS, 2) == hd.dedupe_rows(ROWS, [2, 2, 2])
    assert hd.dedupe_rows(ROWS, 2) == [["A", "B", "C"], ["D", "E"], ["F"]]


def test_a_small_first_limit_leaves_later_rows_more_freedom():
    rows = [["A", "B", "C"], ["C", "B", "A"]]
    assert hd.dedupe_rows(rows, [1, 3]) == [["A", "B", "C"], ["C", "B"]]


def test_a_large_first_limit_blocks_later_rows_that_look_at_it():
    rows = [["A", "B", "C"], ["C", "B", "A"]]
    assert hd.dedupe_rows(rows, [3, 1]) == [["A", "B", "C"], []]


def test_limit_zero_row_only_dedupes_locally():
    rows = [["A", "B", "A"], ["A", "B"]]
    assert hd.dedupe_rows(rows, [0, 1]) == [["A", "B"], ["A", "B"]]


def test_limit_zero_row_does_not_read_the_global_set():
    rows = [["A", "B"], ["A", "B", "A"], ["A", "C"]]
    assert hd.dedupe_rows(rows, [1, 0, 1]) == [["A", "B"], ["A", "B"], ["C"]]


def test_the_limit_counts_kept_titles_in_each_row():
    rows = [["X", "X", "Y", "Z"], ["Y", "Z", "Z", "W"]]
    assert hd.dedupe_rows(rows, [2, 2]) == [["X", "Y", "Z"], ["Z", "W"]]
    assert hd.global_titles(rows, [2, 2]) == {"X", "Y", "Z", "W"}


def test_global_titles_follows_the_per_row_limits():
    assert hd.global_titles(ROWS, [2, 2, 1]) == {"A", "B", "D", "E", "F"}
    assert hd.global_titles(ROWS, [1, 0, 0]) == {"A"}


def test_length_mismatch_raises_value_error():
    with pytest.raises(ValueError):
        hd.dedupe_rows(ROWS, [2, 2])
    with pytest.raises(ValueError):
        hd.dedupe_rows(ROWS, [2, 2, 2, 2])
    with pytest.raises(ValueError):
        hd.dedupe_rows([], [1])
    assert hd.dedupe_rows([], []) == []


def test_limit_list_and_rows_are_not_mutated():
    limits = [2, 2, 1]
    snapshot = [list(r) for r in ROWS]
    hd.dedupe_rows(ROWS, limits)
    assert limits == [2, 2, 1]
    assert ROWS == snapshot


def test_empty_rows_keep_their_place_with_limits():
    assert hd.dedupe_rows([["A"], [], ["A", "B"]], [1, 4, 1]) == [["A"], [], ["B"]]

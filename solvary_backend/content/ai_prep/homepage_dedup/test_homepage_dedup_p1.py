# Provided tests for Part 1: global uniqueness for the first n kept titles.

import homepage_dedup as hd

ROWS = [["A", "B", "A", "C"], ["B", "D", "B", "E"], ["A", "F", "A"]]


def test_worked_example():
    assert hd.dedupe_rows(ROWS, 2) == [["A", "B", "C"], ["D", "E"], ["F"]]


def test_the_fold_counts_kept_titles_not_input_positions():
    assert hd.dedupe_rows([["A", "A", "B", "C"]], 2) == [["A", "B", "C"]]
    assert hd.global_titles([["A", "A", "B", "C"]], 2) == {"A", "B"}


def test_a_globally_dropped_title_does_not_use_up_a_slot():
    rows = [["A", "B"], ["A", "C", "D"]]
    assert hd.dedupe_rows(rows, 2) == [["A", "B"], ["C", "D"]]
    assert hd.global_titles(rows, 2) == {"A", "B", "C", "D"}


def test_titles_below_the_fold_may_repeat_across_rows():
    rows = [["A", "B", "C"], ["D", "E", "C"], ["F", "C", "B"]]
    assert hd.dedupe_rows(rows, 1) == rows
    assert hd.global_titles(rows, 1) == {"A", "D", "F"}


def test_row_local_duplicates_are_dropped_below_the_fold_too():
    assert hd.dedupe_rows([["A", "B", "B", "C", "A", "C"]], 1) == [["A", "B", "C"]]


def test_a_title_dropped_as_global_stays_dropped_later_in_the_row():
    rows = [["A"], ["A", "B", "C", "A"]]
    assert hd.dedupe_rows(rows, 1) == [["A"], ["B", "C"]]


def test_n_zero_means_nothing_is_global():
    rows = [["A", "B", "A"], ["A", "B"]]
    assert hd.dedupe_rows(rows, 0) == [["A", "B"], ["A", "B"]]
    assert hd.global_titles(rows, 0) == set()


def test_n_larger_than_every_row_makes_the_whole_page_unique():
    rows = [["A", "B"], ["B", "C"], ["C", "A", "D"]]
    assert hd.dedupe_rows(rows, 10) == [["A", "B"], ["C"], ["D"]]


def test_rows_are_never_removed_even_when_they_become_empty():
    rows = [["A", "B"], [], ["A", "B"], ["B"]]
    assert hd.dedupe_rows(rows, 5) == [["A", "B"], [], [], []]
    assert hd.dedupe_rows([], 3) == []


def test_input_is_not_mutated_and_rows_are_new_lists():
    rows = [["A", "B", "A"], ["B", "C"]]
    snapshot = [list(r) for r in rows]
    out = hd.dedupe_rows(rows, 2)
    assert rows == snapshot
    assert all(o is not r for o, r in zip(out, rows))


def test_global_titles_matches_the_final_fold():
    rows = [["A", "A", "B", "C"], ["B", "D", "E"]]
    assert hd.global_titles(rows, 2) == {"A", "B", "D", "E"}
    assert hd.global_titles([], 2) == set()

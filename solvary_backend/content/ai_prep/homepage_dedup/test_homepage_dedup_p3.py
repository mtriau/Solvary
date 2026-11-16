# Provided tests for Part 3: exempt rows and the lazy stream.

import itertools

import homepage_dedup as hd
import pytest

ROWS = [["A", "B", "A", "C"], ["B", "D", "B", "E"], ["A", "F", "A"]]


def test_fastprep_style_example_with_an_exempt_row():
    assert hd.dedupe_rows(ROWS, [2, 2, 1], [False, False, True]) == [
        ["A", "B", "C"],
        ["D", "E"],
        ["A", "F"],
    ]


def test_without_exemptions_the_result_matches_part_two():
    assert hd.dedupe_rows(ROWS, [2, 2, 1]) == [["A", "B", "C"], ["D", "E"], ["F"]]
    assert hd.dedupe_rows(ROWS, [2, 2, 1], None) == hd.dedupe_rows(ROWS, [2, 2, 1])
    assert hd.dedupe_rows(ROWS, [2, 2, 1], [False] * 3) == hd.dedupe_rows(ROWS, [2, 2, 1])


def test_exempt_rows_do_not_write_the_global_set():
    rows = [["A", "B"], ["A", "C"]]
    assert hd.dedupe_rows(rows, 1, [True, False]) == [["A", "B"], ["A", "C"]]
    assert hd.global_titles(rows, 1, [True, False]) == {"A"}


def test_exempt_rows_do_not_read_the_global_set():
    rows = [["A"], ["A", "B"]]
    assert hd.dedupe_rows(rows, 1, [False, True]) == [["A"], ["A", "B"]]


def test_exempt_rows_still_dedupe_locally_whatever_their_limit():
    rows = [["A", "A", "B", "B"]]
    assert hd.dedupe_rows(rows, 5, [True]) == [["A", "B"]]
    assert hd.dedupe_rows(rows, 0, [True]) == [["A", "B"]]
    assert hd.global_titles(rows, 5, [True]) == set()


def test_a_later_row_can_reuse_a_title_an_exempt_row_showed_above_its_fold():
    rows = [["A", "B"], ["B", "C"], ["C", "A"]]
    assert hd.dedupe_rows(rows, 2, [True, False, False]) == [["A", "B"], ["B", "C"], ["A"]]


def test_exempt_length_mismatch_raises_value_error():
    with pytest.raises(ValueError):
        hd.dedupe_rows(ROWS, 2, [True, False])
    with pytest.raises(ValueError):
        hd.dedupe_rows(ROWS, 2, [True] * 4)


def test_exempt_flags_and_rows_are_not_mutated():
    flags = [False, False, True]
    snapshot = [list(r) for r in ROWS]
    hd.dedupe_rows(ROWS, [2, 2, 1], flags)
    assert flags == [False, False, True]
    assert ROWS == snapshot


def test_stream_yields_the_same_rows_as_dedupe_rows():
    gen = hd.dedupe_stream(iter(ROWS), [2, 2, 1], [False, False, True])
    assert iter(gen) is gen
    assert list(gen) == hd.dedupe_rows(ROWS, [2, 2, 1], [False, False, True])
    assert list(hd.dedupe_stream(iter(ROWS), 2)) == hd.dedupe_rows(ROWS, 2)


class CountingSource:
    """Yields `total` rows of 20 titles and counts how many were pulled."""

    def __init__(self, total):
        self.total = total
        self.pulled = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.pulled >= self.total:
            raise StopIteration
        i = self.pulled
        self.pulled += 1
        return [f"t{(i * 7 + j) % 1000}" for j in range(20)]


def test_stream_pulls_nothing_until_asked():
    src = CountingSource(50_000)
    gen = hd.dedupe_stream(src, 5)
    assert src.pulled == 0
    next(gen)
    assert src.pulled == 1


def test_stream_pulls_only_the_rows_that_were_consumed():
    src = CountingSource(50_000)
    out = list(itertools.islice(hd.dedupe_stream(src, 5), 100))
    assert len(out) == 100
    assert src.pulled == 100


def test_stream_keeps_one_global_set_across_many_rows():
    out = list(hd.dedupe_stream(CountingSource(3_000), 3))
    assert len(out) == 3_000
    fold = [t for row in out for t in row[:3]]
    assert len(fold) == len(set(fold))
    assert len(fold) <= 1000

import pytest

from chunk import chunk


def test_example():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_exact_multiple():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


def test_size_larger_than_list():
    assert chunk([1, 2], 5) == [[1, 2]]


def test_empty():
    assert chunk([], 3) == []


def test_bad_size_raises():
    with pytest.raises(ValueError):
        chunk([1], 0)
    with pytest.raises(ValueError):
        chunk([1], -2)


def test_chunks_are_copies():
    items = [1, 2, 3]
    chunks = chunk(items, 2)
    chunks[0].append(99)
    assert items == [1, 2, 3]

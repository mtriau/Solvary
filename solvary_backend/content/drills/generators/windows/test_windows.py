from windows import windows


def test_pairs():
    assert windows([1, 2, 3, 4], 2) == [(1, 2), (2, 3), (3, 4)]


def test_triples():
    assert windows([1, 2, 3, 4], 3) == [(1, 2, 3), (2, 3, 4)]


def test_too_short():
    assert windows([1, 2], 3) == []


def test_exact_size():
    assert windows([1, 2, 3], 3) == [(1, 2, 3)]


def test_windows_are_tuples():
    assert all(type(w) is tuple for w in windows([1, 2, 3], 2))


def test_size_one():
    assert windows(["a", "b"], 1) == [("a",), ("b",)]

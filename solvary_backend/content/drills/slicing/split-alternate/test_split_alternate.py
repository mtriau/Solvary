from split_alternate import split_alternate


def test_example():
    assert split_alternate([10, 11, 12, 13, 14]) == ([10, 12, 14], [11, 13])


def test_empty():
    assert split_alternate([]) == ([], [])


def test_single():
    assert split_alternate(["a"]) == (["a"], [])


def test_even_length():
    assert split_alternate([1, 2, 3, 4]) == ([1, 3], [2, 4])


def test_returns_copies():
    items = [1, 2, 3]
    evens, _ = split_alternate(items)
    evens.append(0)
    assert items == [1, 2, 3]

from flatten import flatten


def test_example():
    assert flatten([[1, 2], [3], [], [4, 5]]) == [1, 2, 3, 4, 5]


def test_empty_outer():
    assert flatten([]) == []


def test_all_inner_empty():
    assert flatten([[], []]) == []


def test_single_row():
    assert flatten([[7, 8, 9]]) == [7, 8, 9]


def test_inner_rows_may_be_tuples():
    assert flatten([(1, 2), (3,)]) == [1, 2, 3]


def test_rows_are_not_mutated():
    rows = [[1], [2]]
    flatten(rows)
    assert rows == [[1], [2]]

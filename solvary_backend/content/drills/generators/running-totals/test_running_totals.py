from running_totals import running_totals


def test_example():
    assert running_totals([1, 2, 3, 4]) == [1, 3, 6, 10]


def test_negatives():
    assert running_totals([5, -5, 5]) == [5, 0, 5]


def test_empty():
    assert running_totals([]) == []


def test_single():
    assert running_totals([7]) == [7]


def test_input_is_not_mutated():
    nums = [1, 2]
    running_totals(nums)
    assert nums == [1, 2]

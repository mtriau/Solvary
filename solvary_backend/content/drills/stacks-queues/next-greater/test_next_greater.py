from next_greater import next_greater


def test_example():
    assert next_greater([2, 1, 2, 4, 3]) == [4, 2, 4, -1, -1]


def test_strictly_decreasing():
    assert next_greater([5, 4, 3]) == [-1, -1, -1]


def test_equal_values_do_not_count():
    assert next_greater([3, 3, 4]) == [4, 4, -1]


def test_empty():
    assert next_greater([]) == []


def test_single():
    assert next_greater([7]) == [-1]


def test_linear_time_on_decreasing_input():
    nums = list(range(60_000, 0, -1))
    assert next_greater(nums) == [-1] * 60_000

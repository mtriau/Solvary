from pair_sum_sorted import pair_sum


def test_example():
    assert pair_sum([1, 2, 4, 7, 11], 9) == (2, 7)


def test_no_pair():
    assert pair_sum([1, 2, 4, 7, 11], 100) is None


def test_two_equal_values():
    assert pair_sum([3, 3], 6) == (3, 3)


def test_single_element_cannot_pair_with_itself():
    assert pair_sum([4], 8) is None


def test_empty():
    assert pair_sum([], 0) is None


def test_smallest_first_value_wins():
    assert pair_sum([1, 2, 3, 4, 5], 6) == (1, 5)


def test_negatives():
    assert pair_sum([-8, -3, 0, 2, 5], -1) == (-3, 2)


def test_linear_time():
    nums = list(range(0, 400_000, 2))
    assert pair_sum(nums, 3) is None

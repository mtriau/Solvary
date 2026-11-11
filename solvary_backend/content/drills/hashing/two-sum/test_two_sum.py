from two_sum import two_sum


def test_example():
    assert two_sum([2, 7, 11, 15], 9) == (0, 1)


def test_same_value_twice():
    assert two_sum([3, 3], 6) == (0, 1)


def test_no_pair():
    assert two_sum([1, 2], 7) is None


def test_pair_is_not_the_same_index_twice():
    assert two_sum([4, 1], 8) is None


def test_negative_and_zero():
    assert two_sum([-1, 0, 1], 0) == (0, 2)


def test_earliest_second_index_wins():
    # (1, 2) sums to 7 before (0, 3) does
    assert two_sum([5, 3, 4, 2], 7) == (1, 2)


def test_linear_time():
    nums = list(range(100_000))
    assert two_sum(nums, 199_997) == (99_998, 99_999)

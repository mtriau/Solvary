from subarrays_sum_k import count_subarrays


def test_example():
    assert count_subarrays([1, 1, 1], 2) == 2


def test_single_elements_count():
    assert count_subarrays([1, 2, 3], 3) == 2


def test_zeros():
    assert count_subarrays([0, 0], 0) == 3


def test_negatives():
    assert count_subarrays([1, -1, 1, -1], 0) == 4


def test_no_match():
    assert count_subarrays([1, 2], 10) == 0


def test_empty():
    assert count_subarrays([], 0) == 0


def test_linear_time():
    nums = [1] * 100_000
    assert count_subarrays(nums, 5) == 99_996

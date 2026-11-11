from min_window_sum import min_window_sum


def test_example():
    assert min_window_sum([2, 3, 1, 2, 4, 3], 7) == 2


def test_no_window():
    assert min_window_sum([1, 1, 1], 5) == 0


def test_single_element_suffices():
    assert min_window_sum([10], 7) == 1


def test_whole_array_needed():
    assert min_window_sum([1, 2, 3], 6) == 3


def test_empty():
    assert min_window_sum([], 1) == 0


def test_shrinks_as_far_as_possible():
    assert min_window_sum([1, 4, 4], 4) == 1


def test_linear_time():
    nums = [1] * 200_000
    assert min_window_sum(nums, 150_000) == 150_000

from squares_of_evens import squares_of_evens


def test_example():
    assert squares_of_evens([1, 2, 3, 4]) == [4, 16]


def test_negative_and_zero_are_even():
    assert squares_of_evens([-2, 0, 7]) == [4, 0]


def test_no_evens():
    assert squares_of_evens([1, 3, 5]) == []


def test_empty():
    assert squares_of_evens([]) == []


def test_order_is_preserved():
    assert squares_of_evens([6, 4, 2]) == [36, 16, 4]


def test_input_is_not_mutated():
    nums = [1, 2, 3, 4]
    squares_of_evens(nums)
    assert nums == [1, 2, 3, 4]

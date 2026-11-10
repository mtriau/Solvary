from rotate import rotate


def test_example():
    assert rotate([1, 2, 3, 4, 5], 2) == [3, 4, 5, 1, 2]


def test_negative_rotates_right():
    assert rotate([1, 2, 3], -1) == [3, 1, 2]


def test_k_larger_than_length():
    assert rotate([1, 2, 3], 7) == [2, 3, 1]


def test_empty():
    assert rotate([], 3) == []


def test_zero_and_full_turn_are_identity():
    assert rotate([1, 2, 3], 0) == [1, 2, 3]
    assert rotate([1, 2, 3], 3) == [1, 2, 3]


def test_input_is_not_mutated():
    items = [1, 2, 3]
    rotate(items, 1)
    assert items == [1, 2, 3]

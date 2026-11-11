from to_base import to_base


def test_binary():
    assert to_base(10, 2) == [1, 0, 1, 0]


def test_hex_digits_are_integers():
    assert to_base(255, 16) == [15, 15]


def test_zero():
    assert to_base(0, 7) == [0]


def test_single_digit():
    assert to_base(5, 10) == [5]


def test_power_of_base():
    assert to_base(1000, 10) == [1, 0, 0, 0]


def test_base_36():
    assert to_base(36 * 36 - 1, 36) == [35, 35]

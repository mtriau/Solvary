from euclid_steps import euclid_steps


def test_example():
    assert euclid_steps(12, 8) == 2


def test_order_matters_for_the_count():
    assert euclid_steps(8, 12) == 3


def test_zero_second_argument_takes_no_steps():
    assert euclid_steps(5, 0) == 0


def test_zero_first_argument_takes_one_step():
    assert euclid_steps(0, 5) == 1


def test_coprime():
    assert euclid_steps(7, 3) == 2  # (7,3) -> (3,1) -> (1,0)


def test_consecutive_fibonacci_is_the_worst_case():
    assert euclid_steps(89, 55) == 9

from evaluate_rpn import evaluate_rpn


def test_example():
    assert evaluate_rpn(["2", "1", "+", "3", "*"]) == 9


def test_division_in_expression():
    assert evaluate_rpn(["4", "13", "5", "/", "+"]) == 6


def test_division_truncates_toward_zero():
    assert evaluate_rpn(["7", "-3", "/"]) == -2
    assert evaluate_rpn(["-7", "3", "/"]) == -2


def test_subtraction_order():
    assert evaluate_rpn(["5", "3", "-"]) == 2


def test_single_number():
    assert evaluate_rpn(["42"]) == 42


def test_negative_literal_is_a_number_not_an_operator():
    assert evaluate_rpn(["-4", "2", "*"]) == -8

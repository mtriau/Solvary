from invert import invert


def test_example():
    assert invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}


def test_empty():
    assert invert({}) == {}


def test_input_is_not_mutated():
    original = {"a": 1}
    invert(original)
    assert original == {"a": 1}


def test_order_follows_input():
    assert list(invert({"x": 10, "y": 5})) == [10, 5]

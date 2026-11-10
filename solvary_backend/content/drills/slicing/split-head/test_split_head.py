import pytest

from split_head import split_head


def test_example():
    assert split_head([1, 2, 3]) == (1, [2, 3])


def test_single_element():
    assert split_head(["only"]) == ("only", [])


def test_empty_raises_value_error():
    with pytest.raises(ValueError):
        split_head([])


def test_rest_is_a_list_and_a_copy():
    items = [1, 2]
    _, rest = split_head(items)
    assert type(rest) is list
    rest.append(99)
    assert items == [1, 2]


def test_works_on_any_iterable():
    assert split_head(iter("abc")) == ("a", ["b", "c"])

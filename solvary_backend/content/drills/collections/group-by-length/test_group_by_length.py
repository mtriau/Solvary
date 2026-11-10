import pytest

from group_by_length import group_by_length


def test_example():
    assert group_by_length(["cat", "horse", "dog", "ox"]) == {
        3: ["cat", "dog"],
        5: ["horse"],
        2: ["ox"],
    }


def test_empty():
    assert group_by_length([]) == {}


def test_order_within_group_is_preserved():
    assert group_by_length(["bb", "aa", "cc"]) == {2: ["bb", "aa", "cc"]}


def test_missing_length_raises_key_error():
    groups = group_by_length(["cat"])
    with pytest.raises(KeyError):
        groups[99]


def test_returns_a_plain_dict():
    assert type(group_by_length(["cat"])) is dict

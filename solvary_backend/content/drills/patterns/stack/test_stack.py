import pytest

from stack import Stack


def test_push_pop_order():
    s = Stack()
    s.push(1)
    s.push(2)
    assert s.pop() == 2
    assert s.pop() == 1


def test_len():
    s = Stack()
    assert len(s) == 0
    s.push("a")
    assert len(s) == 1


def test_empty_is_falsy_and_non_empty_is_truthy():
    s = Stack()
    assert not s
    s.push(0)
    assert s


def test_iteration_is_top_first():
    s = Stack()
    for item in (1, 2, 3):
        s.push(item)
    assert list(s) == [3, 2, 1]


def test_peek_does_not_remove():
    s = Stack()
    s.push("x")
    assert s.peek() == "x"
    assert len(s) == 1


def test_pop_and_peek_on_empty_raise_index_error():
    s = Stack()
    with pytest.raises(IndexError):
        s.pop()
    with pytest.raises(IndexError):
        s.peek()

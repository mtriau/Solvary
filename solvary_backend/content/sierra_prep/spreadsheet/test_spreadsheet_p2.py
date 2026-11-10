# Provided tests for Part 2: circular references are rejected.

import pytest
from spreadsheet import CircularReferenceError, Sheet


def test_spec_example():
    s = Sheet()
    s.set("A1", "=B1+1")
    s.set("B1", "=C1")
    with pytest.raises(CircularReferenceError):
        s.set("C1", "=A1")
    assert s.get("A1") == 1
    assert s.refs("C1") == []
    with pytest.raises(CircularReferenceError):
        s.set("A1", "=A1")
    assert s.refs("A1") == ["B1"]


def test_direct_self_reference():
    s = Sheet()
    with pytest.raises(CircularReferenceError):
        s.set("A1", "=A1+1")
    assert s.get("A1") == 0


def test_two_cell_cycle():
    s = Sheet()
    s.set("A1", "=B1")
    with pytest.raises(CircularReferenceError):
        s.set("B1", "=A1")
    assert s.get("B1") == 0


def test_long_cycle():
    s = Sheet()
    for i in range(1, 50):
        s.set(f"A{i}", f"=A{i + 1}")
    with pytest.raises(CircularReferenceError):
        s.set("A50", "=A1")
    s.set("A50", 7)
    assert s.get("A1") == 7


def test_rejected_set_keeps_old_formula():
    s = Sheet()
    s.set("A1", 3)
    s.set("B1", "=A1+1")
    s.set("C1", "=B1")
    with pytest.raises(CircularReferenceError):
        s.set("A1", "=C1")
    assert s.get("A1") == 3
    assert s.get("C1") == 4


def test_diamond_is_not_a_cycle():
    s = Sheet()
    s.set("A1", 1)
    s.set("B1", "=A1")
    s.set("C1", "=A1")
    s.set("D1", "=B1+C1")
    assert s.get("D1") == 2


def test_mentioning_a_cell_twice_is_not_a_cycle():
    s = Sheet()
    s.set("A1", 2)
    s.set("B1", "=A1+A1+A1")
    assert s.get("B1") == 6


def test_number_set_never_raises_and_breaks_chains():
    s = Sheet()
    s.set("A1", "=B1")
    s.set("B1", 5)
    s.set("A1", 9)
    s.set("B1", "=A1")  # A1 is a number now: no cycle
    assert s.get("B1") == 9


def test_cycle_through_unset_cell_is_impossible_but_later_closing_is_caught():
    s = Sheet()
    s.set("A1", "=X1")  # X1 unset
    with pytest.raises(CircularReferenceError):
        s.set("X1", "=A1")
    s.set("X1", "=Y1")
    with pytest.raises(CircularReferenceError):
        s.set("Y1", "=A1+1")


def test_error_is_an_exception_subclass():
    assert issubclass(CircularReferenceError, Exception)

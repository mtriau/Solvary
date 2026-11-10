import dataclasses

import pytest

from point import Point


def test_fields_and_equality():
    assert Point(1, 2).x == 1
    assert Point(1, 2) == Point(1, 2)
    assert Point(1, 2) != Point(2, 1)


def test_keyword_construction():
    assert Point(x=3, y=4) == Point(3, 4)


def test_repr():
    assert repr(Point(1, 2)) == "Point(x=1, y=2)"


def test_distance():
    assert Point(0, 0).distance_to(Point(3, 4)) == 5.0
    assert Point(1, 1).distance_to(Point(1, 1)) == 0.0


def test_hashable_with_value_semantics():
    assert len({Point(1, 1), Point(1, 1), Point(2, 2)}) == 2


def test_frozen():
    p = Point(1, 2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.x = 5

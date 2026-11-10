from itertools import islice

from evens import evens


def test_first_five():
    assert list(islice(evens(), 5)) == [0, 2, 4, 6, 8]


def test_starts_at_zero():
    assert next(iter(evens())) == 0


def test_each_call_starts_fresh():
    a = evens()
    next(a)
    next(a)
    assert next(iter(evens())) == 0


def test_is_lazy_far_out():
    assert next(islice(evens(), 100_000, None)) == 200_000


def test_can_take_zero():
    assert list(islice(evens(), 0)) == []

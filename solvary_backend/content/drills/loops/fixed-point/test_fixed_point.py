import math

import pytest
from fixed_point import fixed_point


def test_cosine_fixed_point():
    assert fixed_point(math.cos, 1.0) == pytest.approx(0.7390851332, abs=1e-6)


def test_newton_sqrt_two():
    assert fixed_point(lambda v: (v + 2 / v) / 2, 1.0) == pytest.approx(math.sqrt(2))


def test_already_fixed_returns_immediately():
    calls = []

    def f(v):
        calls.append(v)
        return v

    assert fixed_point(f, 3.0) == 3.0
    assert len(calls) == 1


def test_gives_up_after_max_steps():
    calls = []

    def diverge(v):
        calls.append(v)
        return v + 1

    with pytest.raises(ValueError):
        fixed_point(diverge, 0.0, max_steps=5)
    assert len(calls) == 5


def test_result_is_within_tolerance_of_its_image():
    f = lambda v: 0.5 * v + 1  # noqa: E731  — converges to 2
    result = fixed_point(f, 10.0, tol=1e-3)
    assert abs(f(result) - result) <= 1e-3
    assert result == pytest.approx(2.0, abs=1e-2)

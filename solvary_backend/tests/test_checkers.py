import pytest

from app.services.execution.checkers import run_checker


def test_exact_match():
    assert run_checker("exact", "1 2\n", "1 2\n", {})
    assert run_checker("exact", "1 2", "1 2\n", {})  # trailing newline normalized
    assert run_checker("exact", "1 2  \n\n", "1 2\n", {})  # trailing ws normalized
    assert not run_checker("exact", "1 3\n", "1 2\n", {})
    assert not run_checker("exact", "1\n2\n", "1 2\n", {})


def test_float_tolerance():
    args = {"epsilon": 1e-6}
    assert run_checker("float_tolerance", "2.5000001\n", "2.5\n", args)
    assert not run_checker("float_tolerance", "2.51\n", "2.5\n", args)
    # non-numeric tokens fall back to string equality
    assert run_checker("float_tolerance", "yes 1.0\n", "yes 1.0000001\n", args)
    assert not run_checker("float_tolerance", "yes\n", "no\n", args)
    # token count mismatch
    assert not run_checker("float_tolerance", "1.0 2.0\n", "1.0\n", args)


def test_unordered_lines():
    assert run_checker("unordered_lines", "b\na\n", "a\nb\n", {})
    assert not run_checker("unordered_lines", "a\na\n", "a\nb\n", {})


def test_unknown_checker_raises():
    with pytest.raises(ValueError):
        run_checker("bogus", "x", "x", {})

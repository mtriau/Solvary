"""
Built-in output checkers — a fixed enum, applied by the judge worker.

Free-form checker code is deliberately NOT supported: under third-party
problem authoring it is arbitrary code execution in our tier. Custom checkers
arrive in phase 2, running inside the sandbox (SOLVARY_DESIGN.md §4).
"""

from collections.abc import Callable


def _normalize(text: str) -> list[str]:
    """Strip trailing whitespace per line and trailing blank lines."""
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def check_exact(actual: str, expected: str, args: dict) -> bool:
    return _normalize(actual) == _normalize(expected)


def check_float_tolerance(actual: str, expected: str, args: dict) -> bool:
    epsilon = float(args.get("epsilon", 1e-6))
    actual_tokens = actual.split()
    expected_tokens = expected.split()
    if len(actual_tokens) != len(expected_tokens):
        return False
    for a, e in zip(actual_tokens, expected_tokens):
        try:
            if abs(float(a) - float(e)) > epsilon:
                return False
        except ValueError:
            if a != e:
                return False
    return True


def check_unordered_lines(actual: str, expected: str, args: dict) -> bool:
    return sorted(_normalize(actual)) == sorted(_normalize(expected))


CHECKERS: dict[str, Callable[[str, str, dict], bool]] = {
    "exact": check_exact,
    "float_tolerance": check_float_tolerance,
    "unordered_lines": check_unordered_lines,
}


def run_checker(name: str, actual: str, expected: str, args: dict) -> bool:
    checker = CHECKERS.get(name)
    if checker is None:
        raise ValueError(f"Unknown checker: {name}")
    return checker(actual, expected, args)

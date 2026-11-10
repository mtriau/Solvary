"""Reference: topic sort.

Key = (prefix, has_number, number). The prefix is everything before the
trailing digit run (so "a1b2" has prefix "a1b" and number 2; "123" has
prefix ""); names without a trailing number sort before numbered names of
the same prefix. `sorted` is stable, so "topic02" and "topic2" (equal keys)
keep their input order. O(n log n).
"""

_DIGITS = "0123456789"


def _key(name: str) -> tuple[str, int, int]:
    prefix = name.rstrip(_DIGITS)
    digits = name[len(prefix):]
    if digits:
        return (prefix, 1, int(digits))
    return (prefix, 0, 0)


def sort_topics(names: list[str]) -> list[str]:
    """Sort by prefix, then numeric suffix. See PROBLEMS.md #4."""
    return sorted(names, key=_key)

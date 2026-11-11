from collections.abc import Hashable, Iterable


def dedupe(items: Iterable[Hashable]) -> list:
    """Unique items in first-seen order."""
    raise NotImplementedError

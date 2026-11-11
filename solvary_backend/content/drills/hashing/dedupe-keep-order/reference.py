from collections.abc import Hashable, Iterable


def dedupe(items: Iterable[Hashable]) -> list:
    return list(dict.fromkeys(items))

from collections import Counter


def first_unique(s: str) -> int:
    counts = Counter(s)
    return next((i for i, c in enumerate(s) if counts[c] == 1), -1)

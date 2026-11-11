def longest_unique(s: str) -> int:
    last: dict[str, int] = {}
    best = left = 0
    for right, c in enumerate(s):
        if c in last:
            left = max(left, last[c] + 1)
        last[c] = right
        best = max(best, right - left + 1)
    return best

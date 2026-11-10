def rotate(items: list, k: int) -> list:
    if not items:
        return []
    k %= len(items)
    return items[k:] + items[:k]

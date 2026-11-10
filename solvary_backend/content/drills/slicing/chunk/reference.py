def chunk(items: list, size: int) -> list[list]:
    if size < 1:
        raise ValueError(f"size must be at least 1, got {size}")
    return [items[i : i + size] for i in range(0, len(items), size)]

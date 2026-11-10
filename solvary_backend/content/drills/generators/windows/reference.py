def windows(items: list, size: int) -> list[tuple]:
    return list(zip(*(items[i:] for i in range(size))))

class TTLCache:
    def __init__(self, capacity: int | None = None) -> None:
        """Part 1 ignores capacity; Part 3 enforces it."""
        raise NotImplementedError

    def put(self, key: str, value, ttl: int, now: int) -> None:
        raise NotImplementedError

    def get(self, key: str, now: int):
        raise NotImplementedError

    def delete(self, key: str, now: int) -> bool:
        raise NotImplementedError

    def size(self, now: int) -> int:
        raise NotImplementedError

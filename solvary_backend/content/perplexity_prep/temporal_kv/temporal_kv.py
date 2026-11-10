class TemporalKV:
    """Part 1: set(key, value, ts) / get(key, ts). See the statement."""

    def __init__(self) -> None:
        raise NotImplementedError

    def set(self, key: str, value: str, ts: int) -> None:
        raise NotImplementedError

    def get(self, key: str, ts: int) -> str | None:
        raise NotImplementedError

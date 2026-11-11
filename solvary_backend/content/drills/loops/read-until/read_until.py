from collections.abc import Callable


def read_until(read: Callable[[], str], sentinel: str) -> list[str]:
    """Lines returned by read() before the first sentinel."""
    raise NotImplementedError

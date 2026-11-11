from collections.abc import Callable


def read_until(read: Callable[[], str], sentinel: str) -> list[str]:
    return list(iter(read, sentinel))

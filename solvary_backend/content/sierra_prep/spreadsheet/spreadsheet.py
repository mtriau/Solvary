from __future__ import annotations


class Sheet:
    """Part 1: cells holding numbers or `=A1+B2+3` formulas. See the statement."""

    def __init__(self) -> None:
        raise NotImplementedError

    def set(self, cell: str, value: int | str) -> None:
        raise NotImplementedError

    def get(self, cell: str) -> int:
        raise NotImplementedError

    def refs(self, cell: str) -> list[str]:
        raise NotImplementedError

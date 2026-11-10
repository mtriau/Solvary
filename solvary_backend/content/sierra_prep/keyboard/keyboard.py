class Keyboard:
    """Part 1: type / backspace / text. See the statement."""

    def __init__(self) -> None:
        raise NotImplementedError

    def type(self, s: str) -> None:
        raise NotImplementedError

    def backspace(self, n: int = 1) -> None:
        raise NotImplementedError

    def text(self) -> str:
        raise NotImplementedError

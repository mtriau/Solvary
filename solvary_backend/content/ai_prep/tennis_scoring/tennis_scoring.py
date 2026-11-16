class Game:
    """Part 1: one game of tennis. See the statement."""

    def record_point(self, player: str) -> None:
        raise NotImplementedError

    def score(self) -> str:
        raise NotImplementedError

    def winner(self) -> str | None:
        raise NotImplementedError

    def points(self) -> tuple[int, int]:
        raise NotImplementedError

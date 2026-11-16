import math

PLAYERS = ("A", "B")
CALLS = ("0", "15", "30", "40")


def _check_player(player: str) -> int:
    if player not in PLAYERS:
        raise ValueError(f"unknown player: {player!r}")
    return PLAYERS.index(player)


def _lead_winner(pts: list[int], target: int) -> str | None:
    """First to `target` points with a lead of at least 2."""
    for i, p in enumerate(PLAYERS):
        if pts[i] >= target and pts[i] - pts[1 - i] >= 2:
            return p
    return None


class Game:
    """One game; with tiebreak=True it is a tiebreak (first to 7, raw points)."""

    def __init__(self, tiebreak: bool = False) -> None:
        self._pts = [0, 0]
        self._target = 7 if tiebreak else 4
        self.tiebreak = tiebreak

    def record_point(self, player: str) -> None:
        idx = _check_player(player)
        if self.winner() is not None:
            raise ValueError("the game is already decided")
        self._pts[idx] += 1

    def winner(self) -> str | None:
        return _lead_winner(self._pts, self._target)

    def points(self) -> tuple[int, int]:
        return self._pts[0], self._pts[1]

    def score(self) -> str:
        win = self.winner()
        if win:
            return f"game {win}"
        a, b = self._pts
        if self.tiebreak:
            return f"{a}-{b}"
        if a >= 3 and b >= 3:
            if a == b:
                return "deuce"
            return f"advantage {'A' if a > b else 'B'}"
        return f"{CALLS[a]}-{CALLS[b]}"


class Set:
    def __init__(self) -> None:
        self._games = [0, 0]
        self._game = Game()

    def record_point(self, player: str) -> None:
        if self.winner() is not None:
            raise ValueError("the set is already decided")
        self._game.record_point(player)
        won = self._game.winner()
        if won is None:
            return
        self._games[PLAYERS.index(won)] += 1
        if self.winner() is None:
            self._game = Game(tiebreak=self._games == [6, 6])

    def winner(self) -> str | None:
        a, b = self._games
        if max(a, b) == 7:  # 7-5 or 7-6 (after a tiebreak)
            return "A" if a > b else "B"
        return _lead_winner(self._games, 6)

    def games(self) -> tuple[int, int]:
        return self._games[0], self._games[1]

    def in_tiebreak(self) -> bool:
        return self.winner() is None and self._game.tiebreak

    def score(self) -> str:
        win = self.winner()
        if win:
            return f"set {win}"
        return f"{self._games[0]}-{self._games[1]}, {self._game.score()}"


class Match:
    def __init__(self, best_of: int = 3) -> None:
        if best_of not in (3, 5):
            raise ValueError("best_of must be 3 or 5")
        self._needed = math.ceil(best_of / 2)
        self._won = [0, 0]
        self._done: list[tuple[int, int]] = []
        self._set = Set()

    def record_point(self, player: str) -> None:
        if self.winner() is not None:
            raise ValueError("the match is already decided")
        self._set.record_point(player)
        won = self._set.winner()
        if won is None:
            return
        self._won[PLAYERS.index(won)] += 1
        self._done.append(self._set.games())
        if self.winner() is None:
            self._set = Set()

    def winner(self) -> str | None:
        for i, p in enumerate(PLAYERS):
            if self._won[i] >= self._needed:
                return p
        return None

    def sets(self) -> list[tuple[int, int]]:
        if self.winner() is not None:
            return list(self._done)
        return self._done + [self._set.games()]

    def score(self) -> str:
        win = self.winner()
        if win:
            return f"match {win}"
        return f"{self._won[0]}-{self._won[1]} sets, {self._set.score()}"


def play(points: str, best_of: int = 3) -> list[str]:
    match = Match(best_of)
    out = []
    for ch in points:
        match.record_point(ch)
        out.append(match.score())
    return out

class Keyboard:
    def __init__(self) -> None:
        self._text = ""
        self._cursor = 0
        self._undo: list[tuple[tuple[str, int], tuple[str, int]]] = []  # (before, after)
        self._redo: list[tuple[tuple[str, int], tuple[str, int]]] = []

    # ── state helpers ──────────────────────────────────────────────

    def _state(self) -> tuple[str, int]:
        return (self._text, self._cursor)

    def _commit(self, before: tuple[str, int]) -> None:
        self._undo.append((before, self._state()))
        self._redo.clear()

    # ── Part 1 (+ cursor-aware in Part 3) ──────────────────────────

    def type(self, s: str) -> None:
        if not s:
            return
        before = self._state()
        self._text = self._text[: self._cursor] + s + self._text[self._cursor :]
        self._cursor += len(s)
        self._commit(before)

    def backspace(self, n: int = 1) -> None:
        k = min(n, self._cursor)
        if k <= 0:
            return
        before = self._state()
        self._text = self._text[: self._cursor - k] + self._text[self._cursor :]
        self._cursor -= k
        self._commit(before)

    def text(self) -> str:
        return self._text

    # ── Part 2 ─────────────────────────────────────────────────────

    def undo(self) -> bool:
        if not self._undo:
            return False
        before, after = self._undo.pop()
        self._redo.append((before, after))
        self._text, self._cursor = before
        return True

    def redo(self) -> bool:
        if not self._redo:
            return False
        before, after = self._redo.pop()
        self._undo.append((before, after))
        self._text, self._cursor = after
        return True

    # ── Part 3 ─────────────────────────────────────────────────────

    def cursor(self) -> int:
        return self._cursor

    def move_left(self, n: int = 1) -> None:
        self._cursor = max(0, self._cursor - n)

    def move_right(self, n: int = 1) -> None:
        self._cursor = min(len(self._text), self._cursor + n)

    def home(self) -> None:
        self._cursor = 0

    def end(self) -> None:
        self._cursor = len(self._text)

    def delete(self, n: int = 1) -> None:
        k = min(n, len(self._text) - self._cursor)
        if k <= 0:
            return
        before = self._state()
        self._text = self._text[: self._cursor] + self._text[self._cursor + k :]
        self._commit(before)

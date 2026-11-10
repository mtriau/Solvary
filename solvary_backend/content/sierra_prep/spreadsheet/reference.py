from __future__ import annotations

import re


class CircularReferenceError(Exception):
    pass


_CELL = re.compile(r"^[A-Z]+[0-9]+$")


class Sheet:
    def __init__(self) -> None:
        # name -> list of terms (int or cell name); a number cell is [int]
        self._cells: dict[str, list] = {}

    # ── Part 1 ─────────────────────────────────────────────────────

    @staticmethod
    def _parse(value) -> list:
        if isinstance(value, int):
            return [value]
        if not isinstance(value, str) or not value.startswith("="):
            raise ValueError(f"bad cell value: {value!r}")
        terms = []
        for raw in value[1:].split("+"):
            t = raw.strip()
            if t.isdigit():
                terms.append(int(t))
            elif _CELL.match(t):
                terms.append(t)
            else:
                raise ValueError(f"bad term: {raw!r}")
        return terms

    def set(self, cell: str, value) -> None:
        terms = self._parse(value)
        new_refs = [t for t in terms if isinstance(t, str)]
        if new_refs and self._reaches(new_refs, cell):
            raise CircularReferenceError(cell)
        self._cells[cell] = terms

    def refs(self, cell: str) -> list[str]:
        out: list[str] = []
        for t in self._cells.get(cell, []):
            if isinstance(t, str) and t not in out:
                out.append(t)
        return out

    def get(self, cell: str) -> int:
        memo: dict[str, int] = {}
        stack = [(cell, False)]
        while stack:
            c, expanded = stack.pop()
            if c in memo:
                continue
            terms = self._cells.get(c, [0])
            if expanded:
                memo[c] = sum(memo[t] if isinstance(t, str) else t for t in terms)
                continue
            stack.append((c, True))
            for t in terms:
                if isinstance(t, str) and t not in memo:
                    stack.append((t, False))
        return memo[cell]

    # ── Part 2 ─────────────────────────────────────────────────────

    def _reaches(self, starts: list[str], target: str) -> bool:
        seen: set[str] = set()
        stack = list(starts)
        while stack:
            c = stack.pop()
            if c == target:
                return True
            if c in seen:
                continue
            seen.add(c)
            stack.extend(self.refs(c))
        return False

    # ── Part 3 ─────────────────────────────────────────────────────

    def dependents(self, cell: str) -> set[str]:
        reverse: dict[str, list[str]] = {}
        for name in self._cells:
            for r in self.refs(name):
                reverse.setdefault(r, []).append(name)
        out: set[str] = set()
        stack = list(reverse.get(cell, []))
        while stack:
            c = stack.pop()
            if c in out:
                continue
            out.add(c)
            stack.extend(reverse.get(c, []))
        return out

    def evaluation_order(self) -> list[str]:
        order: list[str] = []
        done: set[str] = set()
        for root in self._cells:
            if root in done:
                continue
            stack = [(root, False)]
            while stack:
                c, expanded = stack.pop()
                if c in done:
                    continue
                if expanded:
                    done.add(c)
                    order.append(c)
                    continue
                stack.append((c, True))
                for r in self.refs(c):
                    if r in self._cells and r not in done:
                        stack.append((r, False))
        return order

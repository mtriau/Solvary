from itertools import islice

Grid = list[str]
# A state is the whole grid plus, per cell, how many days it has spent in its
# current X (infected) or R (recovered) stretch. Hashable, so cycles are easy.
State = tuple[tuple[str, ...], tuple[tuple[int, ...], ...]]


def _start(grid: Grid) -> State:
    return tuple(grid), tuple((0,) * len(row) for row in grid)


def _next(state: State, rd: int | None, imm: int | None) -> State:
    """One day. Every transition is decided from the previous day's state."""
    rows, ages = state
    cells = [list(row) for row in rows]
    new_ages = [[0] * len(row) for row in rows]
    for i, row in enumerate(rows):
        for j, c in enumerate(row):
            if c == "X":
                age = ages[i][j] + 1 if rd is not None else 0
                if rd is not None and age >= rd:
                    cells[i][j] = "R"  # recovers today, does not spread today
                    continue
                new_ages[i][j] = age
                for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                    if 0 <= ni < len(rows) and 0 <= nj < len(rows[ni]) and rows[ni][nj] == ".":
                        cells[ni][nj] = "X"
            elif c == "R" and imm is not None:
                age = ages[i][j] + 1
                if age >= imm:
                    cells[i][j] = "."  # healthy again, catchable from tomorrow
                else:
                    new_ages[i][j] = age
    return tuple("".join(r) for r in cells), tuple(tuple(r) for r in new_ages)


def _states(grid: Grid, rd: int | None, imm: int | None):
    state = _start(grid)
    while True:
        yield state
        state = _next(state, rd, imm)


def simulate_days(grid: Grid, days: int, recovery_days: int | None = None,
                  immunity_days: int | None = None) -> Grid:
    """The grid after `days` days. The input is never modified."""
    state = next(islice(_states(grid, recovery_days, immunity_days), days, None))
    return list(state[0])


# ── Part 1 ─────────────────────────────────────────────────────────


def step(grid: Grid) -> Grid:
    return simulate_days(grid, 1)


def days_until_stable(grid: Grid, recovery_days: int | None = None,
                      immunity_days: int | None = None) -> int:
    """Days until the state stops changing; -1 if it never does (a cycle)."""
    state = _start(grid)
    seen = {state}
    day = 0
    while True:
        nxt = _next(state, recovery_days, immunity_days)
        if nxt == state:
            return day
        if nxt in seen:
            return -1
        seen.add(nxt)
        state, day = nxt, day + 1


# ── Part 2 ─────────────────────────────────────────────────────────


def count(grid: Grid) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in grid:
        for c in row:
            totals[c] = totals.get(c, 0) + 1
    return totals


# ── Parts 3 and 4 ──────────────────────────────────────────────────


def run(grid: Grid, recovery_days: int | None, days: int,
        immunity_days: int | None = None) -> Grid:
    return simulate_days(grid, days, recovery_days, immunity_days)


# ── Part 5 ─────────────────────────────────────────────────────────


def infected_total(grid: Grid, recovery_days: int | None, days: int,
                   immunity_days: int | None = None) -> int:
    """Cells that are X on at least one of days 0..days."""
    ever: set[tuple[int, int]] = set()
    for state in islice(_states(grid, recovery_days, immunity_days), days + 1):
        for i, row in enumerate(state[0]):
            ever.update((i, j) for j, c in enumerate(row) if c == "X")
    return len(ever)


def _burn(grid: Grid, kind: str, idx: int) -> Grid:
    if kind == "row":
        return ["#" * len(r) if i == idx else r for i, r in enumerate(grid)]
    return [r[:idx] + "#" + r[idx + 1:] for r in grid]


def best_burn(grid: Grid, recovery_days: int | None, days: int,
              immunity_days: int | None = None) -> tuple[str, int]:
    options = [("row", i) for i in range(len(grid))]
    options += [("col", j) for j in range(len(grid[0]))]
    # min() keeps the first of equal keys: rows before columns, low index first.
    return min(options, key=lambda o: infected_total(
        _burn(grid, *o), recovery_days, days, immunity_days))

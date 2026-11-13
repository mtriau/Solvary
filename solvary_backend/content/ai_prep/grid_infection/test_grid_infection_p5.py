# Provided tests for Part 5: counting infected cells and the burn intervention.

import time

import grid_infection as gi

RING = ["...", ".#.", "RX."]


def test_infected_total_counts_cells_that_were_ever_infected():
    grid = ["X..."]
    assert gi.infected_total(grid, None, 0) == 1
    assert gi.infected_total(grid, None, 2) == 3
    assert gi.infected_total(grid, None, 10) == 4


def test_infected_total_includes_cells_that_have_since_recovered():
    assert gi.infected_total(["X..."], 2, 10) == 4
    assert gi.infected_total(["X..."], 2, 2) == 3
    assert gi.infected_total(["X..."], 1, 10) == 1


def test_infected_total_counts_a_reinfected_cell_once_and_skips_walls():
    assert gi.infected_total(RING, 2, 100, 1) == 8
    assert gi.infected_total(RING, 2, 0, 1) == 1
    assert gi.infected_total(["X#."], None, 5) == 1
    assert gi.infected_total([], None, 5) == 0


def test_burning_the_column_of_sources_beats_every_row():
    grid = ["X....", "X....", "X...."]
    assert gi.best_burn(grid, None, 5) == ("col", 0)
    # Sanity: every row burn leaves two full rows to burn through.
    assert gi.infected_total(["#####", "X....", "X...."], None, 5) == 10


def test_burning_the_only_source_row_beats_every_column():
    grid = ["....", "....", "XX.."]
    assert gi.best_burn(grid, None, 6) == ("row", 2)


def test_ties_prefer_rows_then_the_lowest_index():
    # Nothing is infected, so every burn scores zero.
    assert gi.best_burn(["...", "..."], None, 3) == ("row", 0)
    # A lone source: its row and its column both remove it. Rows win.
    assert gi.best_burn(["...", ".X.", "..."], None, 3) == ("row", 1)
    # Burning row 0, row 2, col 0 or col 2 each saves exactly the same.
    assert gi.best_burn(["X..", "...", "..X"], None, 1) == ("row", 0)


def test_the_best_burn_depends_on_the_day_limit():
    grid = ["X...", "....", "....", "...X"]
    # Over one day any of the four border lines through a source ties; row 0 wins.
    assert gi.best_burn(grid, None, 1) == ("row", 0)
    # The answer always matches a brute-force search over every row and column.
    for days in (1, 2, 4):
        assert gi.best_burn(grid, 3, days) == _brute_force(grid, 3, days)


def test_recovery_changes_what_a_burn_is_worth():
    grid = ["..X..", ".....", "....."]
    assert gi.infected_total(grid, 1, 5) == 1
    # With recovery_days=1 nothing ever spreads, so burning the source's row
    # (rows come first) is as good as it gets.
    assert gi.best_burn(grid, 1, 5) == ("row", 0)


def test_best_burn_does_not_modify_its_input_and_returns_a_tuple():
    grid = ["X..", "...", "..X"]
    snapshot = list(grid)
    result = gi.best_burn(grid, 2, 4)
    gi.infected_total(grid, 2, 5)
    assert grid == snapshot
    assert isinstance(result, tuple) and len(result) == 2


def test_sixteen_by_sixteen_search_is_fast_and_optimal():
    grid = ["." * 16 for _ in range(16)]
    grid[2] = "X" + grid[2][1:]
    grid[13] = grid[13][:15] + "X"
    start = time.perf_counter()
    result = gi.best_burn(grid, 4, 12)
    assert time.perf_counter() - start < 1.0
    assert result == _brute_force(grid, 4, 12)


def _burn(grid, kind, idx):
    if kind == "row":
        return ["#" * len(r) if i == idx else r for i, r in enumerate(grid)]
    return [r[:idx] + "#" + r[idx + 1:] for r in grid]


def _brute_force(grid, recovery_days, days):
    options = [("row", i) for i in range(len(grid))] + [("col", j) for j in range(len(grid[0]))]
    scores = [gi.infected_total(_burn(grid, k, i), recovery_days, days) for k, i in options]
    return options[scores.index(min(scores))]

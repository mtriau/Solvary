# Provided tests for Part 2: immune cells, walls and counts.

import time

import grid_infection as gi


def test_immune_cells_never_change_and_block_the_spread():
    assert gi.step(["X#."]) == ["X#."]
    assert gi.step([".#.", "X#.", ".#."]) == ["X#.", "X#.", "X#."]
    assert gi.step(["X.#"]) == ["XX#"]


def test_a_wall_isolates_a_region_and_the_simulation_terminates():
    grid = ["X#.", "X#.", "X#."]
    assert gi.step(grid) == grid
    assert gi.days_until_stable(grid) == 0


def test_fully_enclosed_infection_stays_inside():
    grid = ["###", "#X#", "###"]
    assert gi.days_until_stable(grid) == 0
    grid = ["#####", "#X..#", "#####", "..X.."]
    assert gi.days_until_stable(grid) == 2


def test_spread_goes_around_a_wall_through_the_gap():
    grid = ["X#.", ".#.", "..."]
    assert gi.days_until_stable(grid) == 6
    grid = ["X.#", "..#", "..."]
    assert gi.days_until_stable(grid) == 4


def test_final_state_leaves_unreachable_cells_healthy():
    grid = ["X.#.", "..#.", "..#."]
    days = gi.days_until_stable(grid)
    assert days == 3
    state = grid
    for _ in range(days + 3):
        state = gi.step(state)
    assert state == ["XX#.", "XX#.", "XX#."]


def test_simultaneous_spread_still_holds_next_to_walls():
    assert gi.step(["X.#.X"]) == ["XX#XX"]
    assert gi.step(["X..#"]) == ["XX.#"]


def test_count_reports_each_cell_type_present():
    assert gi.count(["X.#", "..."]) == {"X": 1, ".": 4, "#": 1}
    assert gi.count(["..."]) == {".": 3}
    assert gi.count(["XX", "XX"]) == {"X": 4}


def test_count_of_an_empty_grid_is_empty():
    assert gi.count([]) == {}
    assert gi.count([""]) == {}


def test_count_after_the_spread_has_finished():
    grid = ["X.#.", "..#."]
    state = grid
    for _ in range(gi.days_until_stable(grid)):
        state = gi.step(state)
    assert gi.count(state) == {"X": 4, "#": 2, ".": 2}


def test_walled_forty_by_forty_maze_is_fast_and_correct():
    # Walls on every fourth row, each with a single gap that alternates ends.
    rows = []
    for i in range(40):
        if i % 4 == 3:
            gap = 0 if (i // 4) % 2 else 39
            rows.append("#" * gap + "." + "#" * (39 - gap))
        else:
            rows.append("." * 40)
    rows[0] = "X" + rows[0][1:]
    start = time.perf_counter()
    days = gi.days_until_stable(rows)
    elapsed = time.perf_counter() - start
    assert days == _bfs_days(rows)
    assert elapsed < 1.0


def _bfs_days(rows):
    from collections import deque

    dist = {(i, j): 0 for i, r in enumerate(rows) for j, c in enumerate(r) if c == "X"}
    queue = deque(dist)
    while queue:
        i, j = queue.popleft()
        for ni, nj in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if 0 <= ni < len(rows) and 0 <= nj < len(rows[0]) and rows[ni][nj] == "." \
                    and (ni, nj) not in dist:
                dist[(ni, nj)] = dist[(i, j)] + 1
                queue.append((ni, nj))
    return max(dist.values())

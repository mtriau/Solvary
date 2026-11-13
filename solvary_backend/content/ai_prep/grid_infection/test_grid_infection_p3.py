# Provided tests for Part 3: recovery after recovery_days.

import time

import grid_infection as gi


def test_spec_example_recovery_timeline_on_a_line():
    grid = ["X.."]
    assert gi.run(grid, 2, 0) == ["X.."]
    assert gi.run(grid, 2, 1) == ["XX."]
    assert gi.run(grid, 2, 2) == ["RXX"]
    assert gi.run(grid, 2, 3) == ["RRX"]
    assert gi.run(grid, 2, 4) == ["RRR"]


def test_cell_infected_on_day_zero_is_still_x_after_day_one_and_r_after_day_two():
    assert gi.run(["X"], 2, 1) == ["X"]
    assert gi.run(["X"], 2, 2) == ["R"]
    assert gi.run(["X"], 3, 2) == ["X"]
    assert gi.run(["X"], 3, 3) == ["R"]


def test_a_cell_does_not_spread_on_the_day_it_recovers():
    assert gi.run(["X."], 1, 1) == ["R."]
    assert gi.run(["X.."], 1, 5) == ["R.."]
    # With recovery_days=2 the source spreads on day 1 only.
    assert gi.run(["X..."], 2, 4) == ["RRRX"]
    assert gi.run(["X#.", "..."], 2, 2) == ["R#.", "XX."]


def test_recovered_cells_are_immune_and_block_the_spread():
    assert gi.run(["XR."], 3, 6) == ["RR."]
    assert gi.days_until_stable(["XR."], 3) == 3
    assert gi.run(["RXR"], 2, 5) == ["RRR"]
    assert gi.days_until_stable(["RRR"], 2) == 0


def test_each_cell_has_its_own_clock():
    # Infection reaches cell k on day k; it recovers recovery_days later.
    grid = ["X...."]
    assert gi.run(grid, 3, 3) == ["RXXX."]
    assert gi.run(grid, 3, 4) == ["RRXXX"]
    assert gi.run(grid, 3, 5) == ["RRRXX"]
    assert gi.run(grid, 3, 7) == ["RRRRR"]


def test_days_until_stable_with_recovery_counts_the_recovery_tail():
    assert gi.days_until_stable(["X.."], 2) == 4
    assert gi.days_until_stable(["X...."], 3) == 7
    assert gi.days_until_stable(["X"], 2) == 2
    assert gi.days_until_stable(["X."], 1) == 1


def test_no_recovery_behaves_like_the_earlier_parts():
    assert gi.run(["X..."], None, 2) == ["XXX."]
    assert gi.days_until_stable(["X...."], None) == 4
    assert gi.days_until_stable(["X...."]) == 4


def test_recovery_with_walls_and_counts():
    grid = ["X.#.", "..#."]
    final = gi.run(grid, 2, 10)
    assert final == ["RR#.", "RR#."]
    assert gi.count(final) == {"R": 4, "#": 2, ".": 2}


def test_run_does_not_modify_its_input_and_day_zero_is_a_copy():
    grid = ["X..", "...", "..X"]
    snapshot = list(grid)
    assert gi.run(grid, 2, 3) != snapshot
    assert grid == snapshot
    assert gi.run(grid, 2, 0) == snapshot


def test_forty_by_forty_with_recovery_is_fast():
    grid = ["X" + "." * 39] + ["." * 40] * 39
    start = time.perf_counter()
    assert gi.days_until_stable(grid, 5) == 83
    final = gi.run(grid, 5, 100)
    assert gi.count(final) == {"R": 1600}
    assert time.perf_counter() - start < 1.0

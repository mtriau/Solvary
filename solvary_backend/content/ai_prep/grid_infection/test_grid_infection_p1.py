# Provided tests for Part 1: simultaneous spread and days to stabilise.

import time

import grid_infection as gi


def test_spec_example_centre_cell_spreads_to_four_neighbours():
    grid = ["...", ".X.", "..."]
    assert gi.step(grid) == [".X.", "XXX", ".X."]
    assert gi.step(gi.step(grid)) == ["XXX", "XXX", "XXX"]


def test_spread_is_simultaneous_not_cascading():
    # A cascading update would sweep the whole row in one call.
    assert gi.step(["X..."]) == ["XX.."]
    assert gi.step(["....X"]) == ["...XX"]
    assert gi.step(["X.....", "......"]) == ["XX....", "X....."]


def test_two_sources_meet_in_the_middle():
    assert gi.step(["X..X"]) == ["XXXX"]
    assert gi.step(["X.X"]) == ["XXX"]


def test_diagonals_do_not_spread():
    grid = ["X..", "...", "..."]
    assert gi.step(grid) == ["XX.", "X..", "..."]


def test_step_does_not_modify_its_input():
    grid = ["X..", "...", "..X"]
    snapshot = list(grid)
    result = gi.step(grid)
    gi.days_until_stable(grid)
    assert grid == snapshot
    assert result is not grid


def test_step_edge_cases_leave_the_grid_alone():
    assert gi.step([]) == []
    assert gi.step(["..."]) == ["..."]
    assert gi.step(["XXX"]) == ["XXX"]
    assert gi.step(["X"]) == ["X"]


def test_days_until_stable_on_a_line_and_in_a_box():
    assert gi.days_until_stable(["X...."]) == 4
    assert gi.days_until_stable(["..X.."]) == 2
    assert gi.days_until_stable(["...X."]) == 3
    assert gi.days_until_stable(["X..", "...", "..."]) == 4
    assert gi.days_until_stable(["...", ".X.", "..."]) == 2
    assert gi.days_until_stable(["X....", "....."]) == 5


def test_days_until_stable_is_zero_when_nothing_can_change():
    assert gi.days_until_stable([]) == 0
    assert gi.days_until_stable([""]) == 0
    assert gi.days_until_stable(["...", "..."]) == 0
    assert gi.days_until_stable(["XXX", "XXX"]) == 0
    assert gi.days_until_stable(["X"]) == 0


def test_multiple_sources_stabilise_at_the_farthest_cell():
    assert gi.days_until_stable(["X...X"]) == 2
    assert gi.days_until_stable(["X.......", "........", ".......X"]) == 4


def test_forty_by_forty_grid_is_fast():
    grid = ["X" + "." * 39] + ["." * 40] * 39
    start = time.perf_counter()
    assert gi.days_until_stable(grid) == 78
    assert time.perf_counter() - start < 1.0

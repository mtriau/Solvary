# Provided tests for Part 4: expiring immunity and cycle detection.

import time

import grid_infection as gi

# A ring of eight cells around a wall. One recovered cell trails one infected
# cell; with short immunity the infection chases its own tail forever.
RING = ["...", ".#.", "RX."]


def test_spec_example_a_recovered_cell_is_reinfected_after_immunity_expires():
    grid = ["RX."]
    assert gi.run(grid, 3, 1, 1) == [".XX"]
    assert gi.run(grid, 3, 2, 1) == ["XXX"]


def test_without_expiry_the_same_cell_stays_recovered():
    grid = ["RX."]
    assert gi.run(grid, 3, 2) == ["RXX"]
    assert gi.run(grid, 3, 2, None) == ["RXX"]
    assert gi.days_until_stable(grid, 3) == 4


def test_immunity_lasts_exactly_immunity_days():
    # Infected on day 0, recovers on day 1, immune for two days, healthy on day 3.
    assert gi.run(["X"], 1, 1, 2) == ["R"]
    assert gi.run(["X"], 1, 2, 2) == ["R"]
    assert gi.run(["X"], 1, 3, 2) == ["."]


def test_a_cell_that_just_lost_immunity_is_not_infected_the_same_day():
    # Cell 0 turns healthy on day 2, while its neighbour is still infected.
    # It can only catch the infection on day 3.
    grid = ["RX."]
    assert gi.run(grid, 3, 2, 2) == [".XX"]
    assert gi.run(grid, 3, 3, 2) == [".RX"]


def test_days_until_stable_includes_the_immunity_tail():
    assert gi.days_until_stable(["X"], 1, 2) == 3
    assert gi.days_until_stable(["RX."], 3, 2) == 6
    assert gi.days_until_stable(["X" + "." * 11], 2, 1) == 14


def test_oscillating_grid_never_stabilises():
    assert gi.days_until_stable(RING, 2, 1) == -1


def test_oscillation_is_visible_in_run():
    states = [gi.run(RING, 2, d, 1) for d in range(6)]
    assert states[1] == ["...", ".#.", ".XX"]
    assert states[3] == ["..X", ".#X", "..R"]
    assert states[5] == ["XXR", ".#.", "..."]
    for state in states:
        assert gi.count(state)["#"] == 1
        assert sum(gi.count(state).values()) == 9


def test_the_same_ring_stabilises_when_immunity_never_expires():
    assert gi.days_until_stable(RING, 2) == 8
    assert gi.days_until_stable(RING, 2, None) == 8


def test_run_does_not_modify_its_input():
    snapshot = list(RING)
    gi.run(RING, 2, 50, 1)
    gi.days_until_stable(RING, 2, 1)
    assert RING == snapshot


def test_cycle_detection_is_fast_on_a_forty_row_grid_of_rings():
    # Ten stacked bands of eight walled-in rings, 40 x 32 cells in all.
    band = [row + "#" for row in RING]
    rows = []
    for _ in range(10):
        rows += [line * 8 for line in band[:3]] + ["#" * 32]
    assert len(rows) == 40
    start = time.perf_counter()
    assert gi.days_until_stable(rows, 2, 1) == -1
    assert time.perf_counter() - start < 1.0

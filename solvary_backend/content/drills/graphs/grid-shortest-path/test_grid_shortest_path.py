from grid_shortest_path import shortest_path


def test_example():
    grid = ["..#", ".##", "..."]
    assert shortest_path(grid, (0, 0), (2, 2)) == 4


def test_start_is_goal():
    assert shortest_path(["..#", ".##", "..."], (0, 0), (0, 0)) == 0


def test_unreachable():
    assert shortest_path(["..", "##", ".."], (0, 0), (2, 0)) == -1


def test_straight_line():
    assert shortest_path(["....."], (0, 0), (0, 4)) == 4


def test_detour_around_wall():
    grid = [
        ".#.",
        ".#.",
        "...",
    ]
    assert shortest_path(grid, (0, 0), (0, 2)) == 6


def test_large_open_grid_is_fast():
    n = 300
    grid = ["." * n] * n
    assert shortest_path(grid, (0, 0), (n - 1, n - 1)) == 2 * (n - 1)

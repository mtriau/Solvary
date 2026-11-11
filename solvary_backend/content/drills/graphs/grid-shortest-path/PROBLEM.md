# Shortest path on a grid with BFS

`grid` is a list of equal-length strings: `.` is open, `#` is a wall. Return the fewest 4-directional steps from `start` to `goal` (both `(row, col)` tuples on open cells), or `-1` if unreachable.

### Signature

`def shortest_path(grid: list[str], start: tuple[int, int], goal: tuple[int, int]) -> int`

### Examples

```python
grid = ["..#", ".##", "..."]
shortest_path(grid, (0, 0), (2, 2)) == 4
shortest_path(grid, (0, 0), (0, 0)) == 0
shortest_path(["..", "##", ".."], (0, 0), (2, 0)) == -1
```

### Idiom

BFS with a `deque` of `(cell, distance)`, a `seen` set that you add to **when you enqueue** (not when you pop), and a `DIRS = [(0, 1), (1, 0), (0, -1), (-1, 0)]` constant for the neighbours. Check bounds and walls in one condition.

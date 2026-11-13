# Grid Infection: Part 1

OpenAI asks this problem as five parts in 60 minutes, and finishing the first
three cleanly is the usual bar. A grid of cells holds some infected cells,
and the infection spreads one day at a time. Interviewers check one thing in
particular: the spread must be **simultaneous**, not cascading. A cell that
becomes infected today must not infect anyone until tomorrow. Later parts add
immune cells, recovery, expiring immunity and a burn intervention, so keep the
simulation in one small core you can extend.

### What to implement

Module `grid_infection`:

- `step(grid: list[str]) -> list[str]` returns the grid after one day.
- `days_until_stable(grid: list[str]) -> int` returns the number of days
  after which no cell changes any more (`0` if the grid is already stable).

### Rules

- The grid is a list of equal-length strings. `.` is a healthy cell and `X`
  is an infected cell.
- Each day, every healthy cell with **at least one infected 4-neighbour**
  (up, down, left, right) becomes infected. Infected cells stay infected.
- All cells update at the same moment, based on the grid as it was at the
  start of the day.
- Return a new list; never modify the grid you were given.

### Worked example

```python
grid = ["...",
        ".X.",
        "..."]

step(grid)           # -> [".X.", "XXX", ".X."]
step(step(grid))     # -> ["XXX", "XXX", "XXX"]
days_until_stable(grid)   # -> 2

step(["X..."])       # -> ["XX.."]   (not "XXXX": today's new cell waits)
```

### Clarifications

- **Diagonals?** No. Only the four orthogonal neighbours spread.
- **Is the input modified?** No. `step` returns a fresh list.
- **Empty grid, or a grid with no `X`?** Both are already stable:
  `step([]) == []` and `days_until_stable` is `0`.
- **A grid that is entirely infected?** Stable, so `0` days.
- **Ragged rows?** Not given; all rows have the same length.
- **How big?** Up to about 40 by 40 in the tests, and it must run well under
  a second.

Run the provided tests with **Submit**.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

The classic slip is updating the grid in place so the infection sweeps a whole
row in one call; the `X...` test catches it. A multi-source BFS by level, or
repeated `step` until nothing changes, are both accepted here. Listen for
whether the candidate already thinks of the day counter as separate from the
grid, since the next parts hang more state on each cell.

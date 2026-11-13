# Grid Infection: Part 2

Same module, new cell type. Some cells are now immune, and they change what
"stable" means: whole regions of healthy cells can be walled off and never
get infected. The earlier tests still run, so Part 1 must keep passing.

### What to implement

- `step(grid)` and `days_until_stable(grid)` as before, now aware of `#`.
- `count(grid: list[str]) -> dict[str, int]` returns how many cells of each
  type the grid holds.

### Rules

- `#` is an immune cell. It never changes, never becomes infected, and does
  not spread anything.
- Spread works as before between `.` and `X` through 4-neighbours; an
  infection simply cannot pass through a `#`.
- Healthy cells that no infection can reach stay `.` forever.
  `days_until_stable` must still terminate, and it counts the days until the
  last cell that can change has changed.
- `count` returns a key only for the characters that actually occur.

### Worked example

```python
grid = ["X.#",
        "..#",
        "..."]

days_until_stable(grid)   # -> 4   (the bottom-right cell is the last one in)

step(["X#."])             # -> ["X#."]   (the wall blocks it)
count(["X.#", "..."])     # -> {"X": 1, ".": 4, "#": 1}
count([])                 # -> {}
```

### Clarifications

- **Can an `X` start inside a sealed region?** Yes. It infects that region
  and nothing else. `["###", "#X#", "###"]` is already stable.
- **Do unreachable healthy cells count towards the days?** No. They never
  change, so they never delay stability.
- **Does `count` always list all the types?** No, only those present, so
  `count([])` is `{}`. Key order does not matter.
- **Is the input modified?** Still no.

Run the provided tests with **Submit**; the Part 1 tests run too.

---
Interviewer notes

Check that the candidate does not loop forever on the walled-off grid, which
is what a "while any healthy cell remains" condition does. Stopping when a day
changes nothing is the clean criterion, and it is the same criterion Part 4
generalises. If they used BFS in Part 1, `#` is just a cell the queue refuses
to enter.

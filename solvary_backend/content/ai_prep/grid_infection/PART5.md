# Grid Infection: Part 5

Same module, new decision: before the infection starts you may burn exactly
one row or one column, turning every cell in it into an immune `#`. Choose
the line that leaves the fewest cells ever infected. The earlier tests still
run.

### What to implement

- `infected_total(grid, recovery_days, days, immunity_days=None) -> int`:
  the number of distinct cells that are `X` on at least one of days
  `0 .. days`, inclusive.
- `best_burn(grid, recovery_days, days, immunity_days=None) -> tuple[str, int]`:
  `("row", i)` or `("col", j)` for the single burn that minimises
  `infected_total` after the burn.

### Rules

- The burn happens before day 0: every cell of the chosen line, including any
  infected one, becomes `#`. Then the simulation runs exactly as in Part 4.
- A cell infected twice counts once. Cells burned to `#` are never counted.
- **Ties:** prefer rows over columns, then the lowest index.
- The grid has at least one row and one column. Inputs stay unmodified.

### Worked example

```python
infected_total(["X..."], None, 2)    # -> 3
infected_total(["X..."], 2, 10)      # -> 4  (recovered cells were infected)

grid = ["X....",
        "X....",
        "X...."]
best_burn(grid, None, 5)             # -> ("col", 0)  (all sources burned)

best_burn(["X..", "...", "..X"], None, 1)   # -> ("row", 0)  (a four-way tie)
```

### Clarifications

- **Do I count the burned cells?** No, they are `#` from the start.
- **Can the best burn remove every infection?** Yes, the total is then `0`.
- **Nothing infected at all?** Every option scores 0, so the answer is
  `("row", 0)`.
- **Must I be clever?** No. Trying every row and column with the Part 4
  simulation is fine at test sizes (up to about 16 by 16); name the cost.

Run the provided tests with **Submit**; all earlier tests run too.

---
Interviewer notes

The intended answer is brute force over rows and columns on top of the Part 4
core, which is why the core should be one reusable function. Strong
candidates state the complexity (lines times days times cells) and mention
that for plain BFS a burn only helps by cutting distances, so the full
simulation can be replaced by a multi-source BFS per option. The tie-break is
the usual place for an off-by-one in ordering.

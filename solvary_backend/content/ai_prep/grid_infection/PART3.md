# Grid Infection: Part 3

Same module, new cell type. Infection now ends: an infected cell recovers
after a fixed number of days and becomes `R`. This is the part where the
ordering of events inside a day has to be pinned down, so read the rules
slowly. The Part 1 and Part 2 tests still run.

### What to implement

- `run(grid: list[str], recovery_days: int | None, days: int) -> list[str]`
  returns the grid after `days` days. `recovery_days=None` means infected
  cells never recover (the old behaviour).
- `days_until_stable(grid, recovery_days=None)` returns the number of days
  until the whole state stops changing, as before.

### Rules

- `R` is a recovered cell. It is immune for good: it never becomes infected
  again and does not spread. The grid you are given may already contain `R`.
- Cells that are `X` at the start (day 0) have been infected for 0 days. A
  cell becomes `R` once it has been infected for `recovery_days` days.
- Each day, in this order, from the state at the end of the previous day:
  1. every infected cell's counter goes up by one; those that reach
     `recovery_days` become `R`;
  2. every infected cell that did **not** just recover spreads to its healthy
     4-neighbours; the newly infected start their own counter at 0.
- So a cell infected on day 0 with `recovery_days=2` is still `X` after
  day 1 (and spreads on day 1), is `R` after day 2, and does not spread on
  day 2.
- `days_until_stable` counts days until nothing can change again. Counters
  are part of the state: a lone `X` with `recovery_days=2` is stable only
  after day 2, when it turns `R`.

### Worked example

```python
run(["X.."], 2, 0)   # -> ["X.."]
run(["X.."], 2, 1)   # -> ["XX."]
run(["X.."], 2, 2)   # -> ["RXX"]
run(["X.."], 2, 3)   # -> ["RRX"]
run(["X.."], 2, 4)   # -> ["RRR"]
days_until_stable(["X.."], 2)   # -> 4

run(["X."], 1, 1)    # -> ["R."]   (recovers the day it would first spread)
```

### Clarifications

- **Does a cell spread on the day it recovers?** No.
- **What is `recovery_days=1`?** Infected cells recover the next day without
  ever spreading.
- **Can `R` cells block an infection?** Yes. `["XR."]` never infects the
  third cell.
- **`recovery_days=None`?** Same behaviour as Part 2; `R` never appears.
- **Is the input modified?** No.

Run the provided tests with **Submit**; the earlier tests run too.

---
Interviewer notes

The ordering sentence is the whole part. Candidates who spread first and then
age the cells make recovered cells infect one extra day, which the day-2 and
`recovery_days=1` tests expose. Push for a per-cell age rather than a
separate grid of dates; a tuple of rows plus a tuple of ages is hashable,
which pays off in Part 4.

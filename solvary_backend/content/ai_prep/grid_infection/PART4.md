# Grid Infection: Part 4

Same module, new twist: immunity wears off. A recovered cell turns back into
a healthy `.` after a while and can catch the infection again. That means a
grid can now keep changing forever, so `days_until_stable` needs a way to say
so. The earlier tests still run.

### What to implement

- `run(grid, recovery_days, days, immunity_days=None) -> list[str]`: the grid
  after `days` days. `immunity_days=None` means `R` is permanent, as in Part 3.
- `days_until_stable(grid, recovery_days=None, immunity_days=None) -> int`:
  days until the state stops changing, or `-1` if it never will.

### Rules

- A cell that became `R` on day d is `R` on days d .. d + immunity_days - 1
  and is healthy `.` on day d + immunity_days. Its counter starts at 0 on the
  day it recovers. (Cells that start as `R` count as recovered on day 0.)
- The day-ordering of Part 3 holds, and every cell in a day is decided from
  the state at the end of the previous day. In particular, a cell that
  turns healthy today cannot be infected today; the earliest is tomorrow.
- "State" means the grid and every cell's counter. If a day produces a state
  you have already seen, the simulation is cycling and will never stabilise:
  return `-1`. If a day produces exactly the same state, return the number of
  days that took.

### Worked example

```python
run(["RX."], 3, 1, 1)   # -> [".XX"]   (R expired, X spread right)
run(["RX."], 3, 2, 1)   # -> ["XXX"]   (cell 0 healthy again, reinfected)
run(["RX."], 3, 2)      # -> ["RXX"]   (no expiry: stays recovered)

ring = ["...",
        ".#.",
        "RX."]
days_until_stable(ring, 2, 1)   # -> -1  (the infection chases its tail)
days_until_stable(ring, 2)      # -> 8
```

### Clarifications

- **How do I know a cycle when I see one?** Remember every full state (grid
  and counters); a repeat means the future repeats too.
- **Could the grid repeat while the counters differ?** Then it is not the
  same state and not yet a cycle.
- **Is the input modified?** No.
- **Does `immunity_days=None` still terminate?** Yes; it is Part 3 again.

Run the provided tests with **Submit**; the earlier tests run too.

---
Interviewer notes

Expect a few minutes of debugging the boundary: does a cell that just turned
healthy get infected the same day? The statement says no, and the tests pin
it. The ring is the smallest oscillator the interviewer will usually have in
mind; a candidate who adds a maximum-days cutoff instead of hashing the state
should be asked what the cutoff is for a 1000 by 1000 grid.

# Debug View: Part 3

Flags are not enough; the view needs to show *where* the dead time is and
*how busy* the busiest moment was.

### What to implement

- `gaps(segments) -> list[tuple[int, int]]`: every maximal uncovered
  half-open window strictly between the earliest `start` and the latest
  `end`, in chronological order. `[]` when there is no gap or fewer than two
  segments.
- `max_concurrent(segments) -> int`: the largest number of segments
  covering a single point in time. `0` for empty input.

Both must be O(n log n); inputs go up to 200,000 segments.

### Rules

1. A gap `(a, b)` means no segment covers any point in `[a, b)`: `a` is the
   furthest end reached before it and `b` is the next start. Gaps are
   maximal, so two gaps never touch.
2. Half-open rule for concurrency: a segment ending at `t` and one starting
   at `t` are **not** concurrent at `t`.

### Worked example

```python
segs = [(0, 5, "a"), (3, 8, "b"), (10, 12, "c"), (12, 13, "d"), (15, 16, "e")]
gaps(segs)            # -> [(8, 10), (13, 15)]
max_concurrent(segs)  # -> 2        (a and b over [3, 5))
max_concurrent([(0, 5, "a"), (5, 8, "b")])   # -> 1
```

`c` and `d` touch at 12, so there is no gap between them and they are not
concurrent.

### Clarifications

- **Nested segments and gaps?** `(0, 10), (2, 3), (12, 13)` has one gap,
  `(10, 12)`. The inner segment does not create a gap after 3; track the
  furthest end.
- **Several segments start exactly when another ends.** `(0, 5), (5, 10),
  (5, 6)` has concurrency 2 (the two starting at 5), not 3. If you sweep
  events, process ends at `t` before starts at `t`.
- **Seven identical segments?** Concurrency 7.
- **Unsorted input for `gaps`?** Sort first; the result is chronological.
- **A single segment?** `gaps` is `[]` and `max_concurrent` is `1`.

Run the provided tests with **Submit**.

---
Interviewer notes

The reported assessment stopped at overlap/gap flags; this part is the
natural follow-up. For `max_concurrent`, sort the events so that an end
at `t` is processed before a start at `t`.

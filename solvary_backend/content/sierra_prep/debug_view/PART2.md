# Debug View: Part 2

The view flags two health signals: did anything run concurrently, and was
there dead time?

### What to implement

`coverage_flags(segments) -> tuple[bool, bool]` returning
`(any_overlap, any_gap)`. Texts are ignored. Input is unsorted, with the
same tuple shape as Part 1.

### Rules

1. `any_overlap` is `True` if **some pair** of segments overlaps, with the
   Part 1 meaning: strictly, half-open, so touching windows do not count.
2. `any_gap` is `True` if, between the **earliest `start`** and the
   **latest `end`** across all segments, there is some point in time
   covered by no segment.
3. Fewer than two segments: `(False, False)`.
4. Both values must be real `bool`s (`True` / `False`), not `0` / `1`.
5. Up to 200,000 segments. Sort once, then one pass: O(n log n).

### Worked example

```python
coverage_flags([(0, 5, "a"), (5, 8, "b")])               # -> (False, False)  touching
coverage_flags([(0, 5, "a"), (3, 8, "b")])               # -> (True, False)
coverage_flags([(0, 5, "a"), (6, 8, "b")])               # -> (False, True)   nothing covers [5, 6)
coverage_flags([(0, 5, "a"), (3, 8, "b"), (9, 10, "c")]) # -> (True, True)
```

### Clarifications

- **Segments nested inside a bigger one, like `(0, 10), (2, 3), (4, 5)`.**
  That is an overlap, and there is **no** gap: `(0, 10)` covers everything.
  If you only compare each segment with the previous one's end, you will
  wrongly report a gap at `[3, 4)`. Keep the furthest end reached so far.
- **Identical segments?** They overlap.
- **Does time before the first start or after the last end count as a
  gap?** No. Only the span between the earliest start and the latest end.
- **One segment?** `(False, False)`, by rule 3.

Run the provided tests with **Submit**.

---
Interviewer notes

A contained-interval case breaks the common bug of tracking only the
previous segment's end instead of the furthest end reached:
`[(0, 10), (2, 3), (4, 5)]` has overlaps and no gap.

# Debug View: Part 1

An agent's debug view shows what happened over time. Log segments arrive in
no particular order, each covering a time window and carrying some text.
Merge the ones that overlap into one entry.

### What you are given

A list of tuples `(start, end, text)`:

- `start` and `end` are integers with `0 <= start < end`.
- The window is **half-open**: it covers `start` up to but not including
  `end`. So `[0, 5)` and `[5, 8)` share no point in time.
- `text` is a non-empty string.

### What to implement

`merge_segments(segments) -> list[tuple[int, int, str]]`

### Rules

1. **Sort first,** chronologically: by `start`, then by smaller `end`, then
   by position in the input (a stable sort on `(start, end)` does this).
2. **Merge overlapping segments.** Walking the sorted list, a segment
   overlaps the current merged group if its `start` is **strictly less
   than** the group's current end. Touching windows (`end == next start`)
   do not merge.
3. A merged group spans from its first `start` to the **furthest** `end`
   seen in the group, and its text is the members' texts joined by a single
   space, in sorted order.
4. Return the groups in chronological order, as tuples. Empty input returns
   `[]`. Do not mutate the input list.

### Worked example

```python
merge_segments([(0, 5, "A"), (3, 10, "B"), (12, 15, "C")])
# -> [(0, 10, "A B"), (12, 15, "C")]

merge_segments([(1, 4, "X"), (4, 6, "Y"), (5, 8, "Z")])
# -> [(1, 4, "X"), (4, 8, "Y Z")]
```

In the second example, `Y` starts at 4, exactly where `X` ends, so they do
not merge. `Z` starts at 5, inside `Y`'s window, so they do.

### Clarifications

- **A segment lies entirely inside another, like `(2, 4)` inside
  `(0, 10)`.** They overlap. The merged end stays at 10 and the text is
  `"outer inner"`. Track the furthest end, not the last segment's end.
- **Two segments with the same start?** The one with the smaller `end`
  comes first in the text: `(0, 9, "long")` and `(0, 2, "short")` merge to
  `(0, 9, "short long")`.
- **Same start and same end?** Keep input order.
- **A chain `(0,2) (1,3) (2,4) (3,5)`?** All one group, `(0, 5, "a b c d")`,
  since each starts before the running end.
- **Scale?** 100,000 segments that all merge into one. Sort once, and
  collect texts in a list to join at the end rather than concatenating
  strings repeatedly.
- **Return tuples or lists?** Tuples, as in the examples.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

From the Software Engineer online assessment reported in November 2025:
"a 'Debug View' problem involving time intervals and text sequencing,
with follow-up questions about overlaps and gaps." Half-open semantics
(touching does not merge) is the first thing to confirm with the
candidate.

# Homepage Row Deduplication: Part 2

The same function grows. Product wants a different fold size per row: the top
row may be strictly unique over its first five titles while a long tail row
only cares about its first one. The earlier tests still run, so Part 1 must
keep passing.

### What to implement

- `dedupe_rows(rows, n)` where `n` is now `int | list[int]`. A plain int means
  the same limit for every row, as before. A list holds one limit per row.
- A list whose length differs from `len(rows)` raises `ValueError`.
- `global_titles(rows, n)` accepts the same two forms of `n`.

### Rules

- Row `i` uses limit `n[i]`: its first `n[i]` kept titles are above the fold, and
  everything from Part 1 applies per row (the limit counts kept titles, a title
  dropped as global does not use a slot).
- A row with limit `0` only dedupes locally. It does not read the global set and
  does not write to it.
- Neither `rows` nor the list of limits is modified.

### Worked example

```python
rows = [["A", "B", "A", "C"],
        ["B", "D", "B", "E"],
        ["A", "F", "A"]]

dedupe_rows(rows, [2, 2, 1])
# -> [["A", "B", "C"],
#     ["D", "E"],
#     ["F"]]      # the single slot: A is global so it is dropped, F takes it

dedupe_rows(rows, [2, 2])   # ValueError, three rows but two limits
```

### Clarifications

- **Can a later row with a bigger limit see more than an earlier one wrote?** The
  global set holds only what earlier rows put above *their* folds. With
  `[["A", "B", "C"], ["C", "B", "A"]]` and limits `[1, 3]`, only A is global, so
  the second row becomes `["C", "B"]`.
- **Does a limit-0 row hide its titles from later rows?** No, it writes nothing.
  With limits `[1, 0, 1]` on `[["A", "B"], ["A", "B", "A"], ["A", "C"]]` the third
  row only loses A (global from row 1), giving `["C"]`.
- **Empty `rows` with an empty limit list?** Fine, the result is `[]`.
- **A limit larger than the row?** The whole row is above the fold.

Run the provided tests with **Submit**; the Part 1 tests run too.

---
Interviewer notes

Watch for a candidate who keeps one counter for the whole page rather than one
per row, and for one who special-cases the first row. Handling the list form by
indexing inside the same loop, with the scalar widened up front or looked up per
row, is the clean change. Ask what they would do when the limits come from a
config service and might be wrong: the `ValueError` is the answer, not silent
truncation.

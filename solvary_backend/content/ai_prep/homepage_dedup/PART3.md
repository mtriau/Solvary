# Homepage Row Deduplication: Part 3

The same function grows. Some rows must show whatever they show: "Continue
watching" has to list what you were watching even if the same title headlines a
row above it. Those rows are exempt from global uniqueness. The earlier tests
still run, so Parts 1 and 2 must keep passing. A lazy variant is added as well.

### What to implement

- `dedupe_rows(rows, n, exempt: list[bool] | None = None) -> list[list[str]]`.
  `exempt[i]` marks row `i` as exempt; `None` means no row is exempt. A list
  whose length differs from `len(rows)` raises `ValueError`.
- `global_titles(rows, n, exempt=None)` takes the same `exempt` argument.
- `dedupe_stream(rows_iter, n, exempt=None)` is a generator that yields the
  deduplicated rows one at a time, in order, with the same results as
  `dedupe_rows`. It must not read more rows from `rows_iter` than are needed
  for the rows requested so far, and it must not build the full list.

### Rules

- An exempt row performs only row-local dedup. It neither reads nor writes the
  global set, whatever its limit.
- A non-exempt row behaves as in Part 2. A later non-exempt row may use a title
  that an exempt row showed above its fold, because the exempt row wrote
  nothing.
- With a stream, `n` may be an int or a list, as before. A list that is too short
  or too long is a `ValueError`, raised when the mismatch is discovered while
  the generator is consumed.
- Inputs are not modified.

### Worked example

```python
rows = [["A", "B", "A", "C"],
        ["B", "D", "B", "E"],
        ["A", "F", "A"]]

dedupe_rows(rows, [2, 2, 1], [False, False, True])
# -> [["A", "B", "C"],
#     ["D", "E"],
#     ["A", "F"]]     # the exempt row keeps A; only its repeated A is dropped

gen = dedupe_stream(iter(rows), 2)
next(gen)             # -> ["A", "B", "C"], exactly one row has been pulled
```

### Clarifications

- **Does an exempt row's limit matter?** No. The limit only controls how many
  titles are checked against the global set, and an exempt row checks none.
- **Does the exempt row's title block later rows?** No. With `n = 1` and
  `[["A", "B"], ["A", "C"]]`, exempting row 1 gives `[["A", "B"], ["A", "C"]]`.
- **What does `global_titles` return for exempt rows?** Their titles are not in
  the set.
- **Does `dedupe_stream` pull anything when it is created?** No. Nothing is read
  until the first `next`.

Run the provided tests with **Submit**; the Part 1 and Part 2 tests run too.

---
Interviewer notes

A single flag check around the global read and write is the whole change; a
candidate who copies the loop for exempt rows is carrying risk. For the stream,
the one global set is the only state that grows, and the point is that nothing
else does. Verbal Part 4 (the real follow-up): millions of titles, state
distributed over many servers, can a Bloom filter replace the set, which error
direction is acceptable (a false positive drops a title that was not a
duplicate), and how rows and the shared set would be sharded.

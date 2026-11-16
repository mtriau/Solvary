# Homepage Row Deduplication: Part 1

A streaming homepage is a stack of rows, and the same title should not greet
the viewer twice in the part of the page they see first. This is the shape of
Netflix's open-book "problem-solving" screen: the interviewer expects about 15
minutes of clarifying questions before any code, a single pass with a global
set, and tests you write yourself. A candidate who shipped working code but
barely talked it through was still turned down, because the screen is judged
on communication. Do the same here: read the rules, settle the edge cases
below, then code.

### What to implement

- `dedupe_rows(rows: list[list[str]], n: int) -> list[list[str]]` returns the
  deduplicated rows, in the same order, as new lists.
- `global_titles(rows: list[list[str]], n: int) -> set[str]` returns the set of
  titles that ended up above the fold anywhere on the page.

`rows` is a list of rows, each an ordered list of title ids. Rows are processed
top to bottom, titles left to right.

### Rules

- **Row-local uniqueness, everywhere.** Only the first occurrence of a title in
  a row counts. Every later occurrence in that row is dropped.
- **The fold.** The first `n` *kept* titles of a row are above the fold. Such a
  title must also be absent from the global set (the above-the-fold titles of
  all earlier rows); if it is, it is dropped, otherwise it is kept and added to
  the global set.
- **Below the fold** (kept titles after the first `n`): only the row-local rule
  applies. They are not checked against, and not added to, the global set.
- A title dropped because it was already global does **not** use up one of the
  `n` slots: the next candidate takes it.
- `n = 0` means nothing is global. Rows are never removed, even if they end up
  empty. The input is not modified.

### Worked example

```python
rows = [["A", "B", "A", "C"],
        ["B", "D", "B", "E"],
        ["A", "F", "A"]]

dedupe_rows(rows, 2)
# -> [["A", "B", "C"],   # A and B are above the fold, C is below
#     ["D", "E"],        # B is global, so D and E fill the two slots
#     ["F"]]             # A is global, F takes the slot, the second A is a row duplicate
global_titles(rows, 2)   # -> {"A", "B", "D", "E", "F"}
```

### Clarifications

- **Does the fold count input positions or kept titles?** Kept titles. In
  `["A", "A", "B", "C"]` with `n = 2`, A and B are above the fold, not A and A.
- **Does a title dropped as global consume a slot?** No. In the second row of
  `[["A", "B"], ["A", "C", "D"]]` with `n = 2`, A is dropped and C and D both
  take slots, giving `["C", "D"]`.
- **Can a title repeat across rows below the fold?** Yes. Only above-the-fold
  titles are global.
- **A title dropped as global shows up again later in the same row?** It stays
  dropped: the first occurrence in a row decides. `["A", "B", "C", "A"]` after a
  row that showed A above the fold, with `n = 1`, becomes `["B", "C"]`.
- **Empty rows?** Kept, as empty lists. `dedupe_rows([], n)` is `[]`.
- **Is the input modified?** No.

Run the provided tests with **Submit**.

---
Interviewer notes

The trap is counting input positions instead of kept titles: the row
`["A", "A", "B", "C"]` has only A and B above the fold with `n = 2`. Make the
candidate ask about it, and about whether a globally dropped title uses a slot,
before they type; the screen scores that conversation as much as the code. Close
with the scale question (verbal): millions of titles, state spread over many
servers, would a Bloom filter do, and what does a false positive cost on a
homepage.

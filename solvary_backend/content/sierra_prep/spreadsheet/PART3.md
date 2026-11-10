# Spreadsheet: Part 3

Real sheets are deep and wide. Make evaluation robust and expose the
dependency graph.

### What to implement

1. **`get` must scale.** It has to handle a reference chain **1,500 cells
   deep** (`A1 = A0+1`, `A2 = A1+1`, ...) and a **doubling diamond** 60
   levels deep (`B1 = B0+B0`, `B2 = B1+B1`, ...) without hitting the
   recursion limit or taking exponential time. Evaluate iteratively
   (explicit stack) and memoize each cell's value within one `get` call.
2. `dependents(cell: str) -> set[str]`: every **set** cell whose value
   depends on `cell`, directly or transitively. Empty set if none.
3. `evaluation_order() -> list[str]`: every **set** cell exactly once, in
   an order where each cell comes **after** every set cell it references (a
   topological order). Any valid order is accepted.

### Rules

- The sandbox's recursion limit is the default 1,000. Do not rely on
  raising it.
- `dependents(cell)` works for an unset `cell` too: if `A1 = "=X1+1"` and
  `B1 = "=A1"`, then `dependents("X1")` is `{"A1", "B1"}`. It never
  includes `cell` itself and reflects the current formulas.
- References to unset cells do not constrain `evaluation_order` (only set
  cells appear in it).
- `evaluation_order()` on an empty sheet is `[]`. It too must cope with
  chains over 1,000 cells long.

### Worked example

```python
s = Sheet()
s.set("A1", 1); s.set("A2", "=A1+1"); s.set("A3", "=A2+A1"); s.set("Z1", 7)
s.dependents("A1")        # -> {"A2", "A3"}
s.dependents("Z1")        # -> set()
s.evaluation_order()      # -> e.g. ["A1", "A2", "A3", "Z1"] or ["Z1", "A1", "A2", "A3"]
```

### Clarifications

- **Why is the diamond exponential?** `B60` references `B59` twice, which
  references `B58` twice, and so on: 2^60 term evaluations without
  memoization. With a per-call memo it is 61 evaluations.
- **Can the memo live across calls?** It can, but then every `set` must
  invalidate it correctly. A memo created fresh inside each `get` is the
  simpler safe choice.
- **Does `dependents` have to be incremental?** No. Building the reverse
  graph by scanning all cells on each call is acceptable.
- **How is `evaluation_order` checked?** Its cells must be exactly the set
  cells, each once, and for every cell every set cell it references must
  come earlier.
- **Does Part 2's cycle check also need to handle long chains?** Yes.
  1,500-cell chains are built with `set` in this part's tests, so make the
  check iterative as well.

Run the provided tests with **Submit**.

---
Interviewer notes

Follow-ups a Staff-level interviewer adds: the recursion limit (the
sandbox's is 1,000), repeated sub-expressions, and the reverse graph.
`dependents` can be computed by scanning all cells; no need for an
incremental index.

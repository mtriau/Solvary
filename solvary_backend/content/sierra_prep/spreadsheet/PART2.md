# Spreadsheet: Part 2

Reject circular references.

### What to implement

- Define `class CircularReferenceError(Exception)` in your module (the
  tests import it from there).
- `set(cell, formula)` must raise `CircularReferenceError` if the new
  formula would make `cell` depend on itself, either directly
  (`A1 = "=A1"`) or through any chain of references
  (`A1 -> B1 -> C1 -> A1`).

### Rules

1. **The check happens at `set` time,** using the formulas currently in the
   sheet. Ask: starting from the new formula's refs and following existing
   refs transitively, can I reach `cell`? If yes, raise.
2. **A rejected `set` leaves the sheet unchanged.** The cell keeps its old
   contents, or stays unset. `get` and `refs` on it behave as before the
   attempt.
3. **Not circular:** a formula that mentions the same cell twice
   (`"=A1+A1"`), or a "diamond" where two paths lead to the same cell
   (`D1 = B1 + C1`, `B1 = A1`, `C1 = A1`).
4. **Setting a cell to a plain number never raises,** and may break an
   existing dependency chain. That is fine: cycles are only ever created by
   formulas.
5. A reference to an **unset** cell still counts as an edge. `A1 = "=X1"`
   with `X1` unset is fine, but a later `X1 = "=A1"` is circular.

### Worked example

```python
s = Sheet()
s.set("A1", "=B1+1")
s.set("B1", "=C1")
s.set("C1", "=A1")     # raises CircularReferenceError; C1 stays unset
s.get("A1")            # -> 1       (B1 -> C1 -> 0)
s.set("A1", "=A1")     # raises; A1 is still "=B1+1"
```

### Clarifications

- **`set("A1", "=A1+1")` on a brand-new sheet?** Raises. `A1` depends on
  itself whether or not it had a value before. `get("A1")` is then `0`.
- **Does the check need to be fast?** Brute force is fine here: walk the
  reference graph from the new formula's refs with a visited set. Cycles of
  about 50 cells appear in the tests. Part 3 raises the bar.
- **Should the cell's old formula be considered during the check?** No.
  Only the new formula for `cell` and the current formulas of every other
  cell.
- **Could an existing cycle already be in the sheet?** No. Every `set` is
  checked, so the sheet is always acyclic.
- **Error message or attributes?** Not checked. Any
  `CircularReferenceError` instance is fine.

Run the provided tests with **Submit**.

---
Interviewer notes

The reported question. "Start with brute force" was explicitly allowed:
walking the reference graph from the new formula's refs and looking for
the cell is enough. Ask about complexity if they finish early; the
iterative DFS matters in Part 3.

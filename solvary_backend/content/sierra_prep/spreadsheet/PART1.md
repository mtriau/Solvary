# Spreadsheet: Part 1

A tiny spreadsheet: cells hold integers or formulas that add other cells
together. This part builds the model; the real question (circular
references) is Part 2, so keep the parsing quick.

### What to implement

`class Sheet`:

- `set(cell: str, value: int | str) -> None`: store a value in a cell.
  Setting a cell again replaces its contents.
- `get(cell: str) -> int`: the cell's current value.
- `refs(cell: str) -> list[str]`: the cell names a formula references
  **directly**, in order of first appearance, without duplicates. `[]` for
  a number cell or an unset cell.

### Input format

- A **cell name** is uppercase letters followed by digits: `"A1"`,
  `"BC12"`, `"C100"`.
- A **value** is either a Python `int`, or a **formula string**: `"="`
  followed by one or more terms joined by `"+"`. Each term is a cell name or
  a non-negative integer. Spaces around terms are allowed:
  `"= A1 +  3 + A1 "` is valid.
- Addition is the only operator. Inputs are always well-formed; no
  validation is required.

### Evaluation rules

1. A number cell's value is its number.
2. A formula's value is the sum of its terms; a cell term contributes that
   cell's value, evaluated the same way.
3. A cell that was never set has value `0` and no refs. A formula may
   reference such a cell.
4. **Evaluation is lazy:** `get` always reflects the current contents of
   every cell. Changing `A1` later changes every formula that depends on it.
   Do not cache values across `set` calls unless you invalidate correctly.

### Worked example

```python
s = Sheet()
s.set("A1", 5)
s.set("A2", "=A1 + 10")
s.set("A3", "=A1+A2+A1")
s.get("A3")      # -> 25        5 + 15 + 5
s.refs("A3")     # -> ["A1", "A2"]
s.set("A1", 1)
s.get("A3")      # -> 13        1 + 11 + 1
s.get("Z9")      # -> 0
```

### Clarifications

- **Can a formula have constants only?** Yes: `"=1+2+3"` is 6 with
  `refs == []`.
- **Can a formula be a single cell, `"=C1"`?** Yes.
- **Is a cell ever set to a numeric string like `"5"`?** No. Numbers arrive
  as `int`, formulas as strings starting with `"="`.
- **Negative numbers, subtraction, multiplication, parentheses?** None of
  those.
- **Replace a formula with a number?** Allowed; `refs` becomes `[]`.
- **Set a formula before the cells it references exist?** Allowed. They
  read as 0 until set.
- **Can a formula reference itself in this part?** Assume not; Part 2
  handles it.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

Reconstructed from the Agent Engineer screen (2024 to early 2025):
"Imagine an Excel-style spreadsheet where cells can reference other
cells. How would you detect whether there's a circular reference?" Part 1
builds the model; Part 2 is the reported question. Parsing should take
five minutes, not fifteen.

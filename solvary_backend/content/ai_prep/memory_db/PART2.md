# In-Memory Database: Part 2

The same `MemoryDB` class grows. Level 2 is about reading a whole record
back: list its fields in a deterministic format and filter them by name
prefix. Earlier tests still run, so `set`, `get` and `delete` must keep
behaving exactly as before.

### What to implement

- `scan(key: str) -> list[str]`: every field of the record, as strings of the
  form `"field(value)"`, sorted by field name.
- `scan_by_prefix(key: str, prefix: str) -> list[str]`: the same, but only
  fields whose name starts with `prefix`.

### Rules

- Sorting is by field name, using plain string comparison (so `"B"` sorts
  before `"a"`, and `"a10"` before `"a2"`). Not by value, not by insertion
  order.
- The format is the field name, then the value in parentheses, with no
  spaces: `"name(Ada)"`.
- An unknown key, a record with no fields left, or a prefix that matches
  nothing gives an empty list `[]`, never `None`.
- Prefix matching is case-sensitive and anchored at the start of the field
  name. The empty prefix `""` matches every field. A field named exactly the
  prefix matches.
- Each call returns a new list; the caller may modify it.

### Worked example

```python
db = MemoryDB()
db.set("sensor", "temp_min", "10")
db.set("sensor", "name", "roof")
db.set("sensor", "temp_max", "30")
db.scan("sensor")                       # -> ["name(roof)", "temp_max(30)", "temp_min(10)"]
db.scan_by_prefix("sensor", "temp")     # -> ["temp_max(30)", "temp_min(10)"]
db.scan_by_prefix("sensor", "x")        # -> []
db.scan("missing")                      # -> []
```

### Clarifications

- **Case-insensitive prefix?** No. `"n"` does not match `"Name"`.
- **Natural sort for numbers?** No. Plain string order: `"a10"` comes before
  `"a2"`.
- **What if the value contains parentheses?** Not tested; just concatenate.
- **Does a scan after deleting the last field return `[]`?** Yes.
- **Should `scan` be implemented through `scan_by_prefix`?** Your call. The
  empty prefix makes it a one-liner.

Run the provided tests with **Submit**. The Part 1 tests run too.

---
Interviewer notes

About 18 minutes in the assessment. Graders watch that `scan` and
`scan_by_prefix` share one code path rather than being two copies, because
level 3 needs timestamped versions of both. Candidates stall on sorting
(sort the field names, not the formatted strings: `"a1(x)"` and `"a(y)"` would
swap) and on returning `None` for an unknown key.

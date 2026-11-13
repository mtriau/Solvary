# In-Memory Database: Part 1

This mirrors the CodeSignal four-level industry coding assessment: one class,
`MemoryDB`, that grows over four levels in 90 minutes. A level unlocks when its
suite is green, and every later suite re-runs the earlier tests, so you can
never trade an old level for a new one. Three clean levels beat four broken
ones. Level 1 is the foundation: a store of records, each record a set of
string fields. Keep the data model simple but think ahead: later levels attach
timestamps and expiry times to each field.

### What to implement

In `memory_db.py`, class `MemoryDB` (constructed with no arguments):

- `set(key: str, field: str, value: str) -> None`: store `value` in `field`
  of the record `key`, creating the record or field if needed and replacing
  any previous value.
- `get(key: str, field: str) -> str | None`: the value, or `None` if the
  record or the field does not exist.
- `delete(key: str, field: str) -> bool`: remove the field. Return `True` if
  it existed, `False` otherwise.

### Rules

- Records are independent of each other, and fields within a record are
  independent of each other.
- A record with no fields left no longer exists (it behaves like an unknown
  key).
- An empty string is a legitimate value. Only a missing field gives `None`.
- Do not change these signatures later: the next levels add methods to the
  same class.

### Worked example

```python
db = MemoryDB()
db.set("user:1", "name", "Ada")
db.set("user:1", "city", "London")
db.get("user:1", "name")        # -> "Ada"
db.get("user:1", "email")       # -> None
db.delete("user:1", "city")     # -> True
db.delete("user:1", "city")     # -> False
db.get("user:2", "name")        # -> None
```

### Clarifications

- **Can a later `set` change the value?** Yes, it overwrites.
- **What does `delete` return for an unknown key?** `False`.
- **Do I need to store the order fields were added in?** No. Level 2 sorts by
  field name.
- **Can I use a dict of dicts?** Yes. It is the expected starting point.
- **Is `""` the same as missing?** No. `get` returns `""`, and `delete` returns
  `True`.

Run the provided tests with **Submit**; later levels come with their own test
files.

---
Interviewer notes

Level 1 should take about 12 minutes; graders watch the speed and the shape
of the data model, not the algorithm. Candidates stall on the return values
(`delete` returning `True` only if the field existed) and on `""` versus
`None`. A nested dict is fine; a candidate who already stores a small record
per field instead of a bare string is thinking about level 3.

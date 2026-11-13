# In-Memory Database: Part 3

The same `MemoryDB` class grows: time enters. Every field can now carry a
timestamp and an optional time to live (TTL), and reads happen "at" a
moment, so an expired field is invisible. This is the level that separates
candidates: the boundaries are exact, and the level 1 and 2 tests still
run, so the old methods must keep working. Budget about 30 minutes, and
think about how to make the old methods a special case of the new ones
instead of a second copy.

### What to implement

- `set_at(key, field, value, timestamp) -> None`: like `set`, with no expiry.
- `set_at_with_ttl(key, field, value, timestamp, ttl) -> None`: like
  `set_at`, but the field is alive only for times `t` with
  `timestamp <= t < timestamp + ttl` (half-open).
- `delete_at(key, field, timestamp) -> bool`: like `delete`: `True` if the
  field existed (and was alive) at `timestamp`, else `False`.
- `get_at(key, field, timestamp) -> str | None`: the value if the field is
  alive at `timestamp`, else `None`.
- `scan_at(key, timestamp) -> list[str]` and
  `scan_by_prefix_at(key, prefix, timestamp) -> list[str]`: like `scan` and
  `scan_by_prefix`, listing only fields alive at `timestamp`.

`timestamp` and `ttl` are integers, `ttl >= 1`.

### Rules

- A field set with `set_at_with_ttl("k", "f", "v", 10, 5)` is alive at 10
  through 14 and gone at 15 (`timestamp + ttl`).
- A later `set_at` or `set_at_with_ttl` of the same field replaces the value
  **and** the TTL. A plain `set_at` therefore makes the field permanent,
  even if it carried a TTL before. A new TTL counts from the new timestamp.
- Deleting a field removes its TTL with it: a later set starts fresh.
- Timestamps across all calls are strictly increasing, so you never see
  time go backwards, and you never need to look at the past.
- **The old methods are the `_at` methods at "now".** `set`, `get`, `delete`,
  `scan` and `scan_by_prefix` behave as `set_at`, `get_at`, `delete_at`,
  `scan_at` and `scan_by_prefix_at` evaluated at the largest timestamp
  seen so far in any call (0 if none). A field written with `set` has no
  TTL.

### Worked example

```python
db = MemoryDB()
db.set_at_with_ttl("k", "session", "abc", 10, 5)   # alive for 10..14
db.set_at("k", "name", "Ada", 11)                  # permanent
db.get_at("k", "session", 14)                      # -> "abc"
db.get_at("k", "session", 15)                      # -> None
db.scan_at("k", 12)                                # -> ["name(Ada)", "session(abc)"]
db.scan_at("k", 15)                                # -> ["name(Ada)"]
db.set_at_with_ttl("k", "name", "Bob", 16, 2)      # replaces value and TTL
db.get_at("k", "name", 18)                         # -> None
db.get("k", "name")                                # -> None (now = 18)
```

### Clarifications

- **Is the end of the TTL inclusive?** No. At `timestamp + ttl` the field is
  gone; at `timestamp + ttl - 1` it is still there.
- **Overwriting a field before it expires?** The new TTL (or no TTL) fully
  replaces the old one; it is not extended or minimised.
- **Overwriting after it expired?** It is simply a new field.
- **`delete_at` on an expired field?** `False`: it did not exist at that time.
- **`delete_at` on the last live tick?** `True`.
- **What time do the old methods use?** The largest timestamp seen so far in
  any call, 0 before the first timestamped call. Tests for levels 1 and 2
  never use TTLs.
- **Does a read at a timestamp advance "now"?** Yes, any timestamped call
  does.
- **Must expired fields be physically removed?** No. Only their visibility is
  tested.

Run the provided tests with **Submit**. The Part 1 and Part 2 tests run too.

---
Interviewer notes

The reported traps are the boundary (`<` versus `<=` at `timestamp + ttl`),
an overwrite that must reset the TTL (including a plain set after a TTL set),
and `delete_at` returning `False` for an already expired field. Graders
watch whether the candidate routes level 1 and 2 through the new code
instead of duplicating it, and whether the data model needed a rewrite;
storing `(value, expires_at)` per field makes this a small extension.

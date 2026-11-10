### Why this is idiomatic

- `partition("=")` splits on the first `=` and always returns three parts, so the unpacking `key, _, value = ...` never raises. `split("=")` would need an index and a length check.
- `int(value)` tolerates surrounding whitespace (`int(" 1 ")` is `1`), so only the key needs `strip()`.
- `if not item.strip(): continue` uses truthiness for "blank" and keeps the happy path unindented.
- A plain loop is right here. The dict comprehension version needs a nested trick to bind the partition result and reads worse.

### The habit

Reach for `partition` when you split on the first occurrence of a separator and want exactly two sides.

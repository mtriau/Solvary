# Time-Versioned KV Store: Part 2 (reveal verbatim)

- `delete(key, ts)`: from time `ts` onward the key has no value, until a
  later `set`. `get` in that window returns None. Timestamps for `delete`
  follow the same non-decreasing rule. Deleting a key that was never set is
  allowed: it records a tombstone.
- `get_range(key, start, end) -> list[tuple[int, str | None]]`: every
  change to the key with `start <= ts <= end` (inclusive both ends), in
  time order, as `(ts, value)`; a delete appears as `(ts, None)`. Only
  change points: a value that was already in effect before `start` is not
  included. Empty list for an unknown key, an empty window, or
  `start > end`.
- A `set` and a `delete` at the same timestamp are both change points, in
  call order; the later call wins for `get`.

Provided tests: `test_temporal_kv_p2.py` (copy into `temporal_kv/`), then
`pytest temporal_kv -q`.

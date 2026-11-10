# Time-Versioned KV Store: Part 3 (reveal verbatim)

- `restore(ts)`: discard every mutation (set or delete) with timestamp
  strictly greater than `ts`, across all keys, as if they never happened.
  A mutation whose timestamp equals `ts` is kept. Later writes resume from
  `ts` (still non-decreasing), so a `set` at exactly `ts` after a restore
  is legal. `restore` before anything happened is a no-op.
- Up to 200K mutations and many restores: a restore should cost
  proportional to what it discards, not to the number of keys.

Provided tests: `test_temporal_kv_p3.py` (copy into `temporal_kv/`), then
`pytest temporal_kv -q`.

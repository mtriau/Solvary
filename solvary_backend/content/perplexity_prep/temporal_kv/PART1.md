# Time-Versioned Key-Value Store: Part 1

Implement `TemporalKV`, a key-value store where every write is stamped with
a time and reads ask for the value **as of** a time.

- `set(key: str, value: str, ts: int) -> None`
  Record that `key` has `value` from time `ts` onward.
- `get(key: str, ts: int) -> str | None`
  Return the value of `key` as of time `ts`: the value from the most recent
  `set` whose timestamp is `<= ts`. Return `None` if no such set exists.

Timestamps passed to `set` are **non-decreasing** across all calls (over all
keys). The same timestamp may repeat; when two sets of the same key share a
timestamp, the later call wins. `get` may be called with any timestamp, in
any order.

```python
kv = TemporalKV()
kv.set("a", "1", 1)
kv.set("a", "2", 5)
kv.set("b", "x", 5)
kv.get("a", 0)      # -> None
kv.get("a", 1)      # -> "1"
kv.get("a", 3)      # -> "1"
kv.get("a", 5)      # -> "2"
kv.get("a", 100)    # -> "2"
kv.get("b", 4)      # -> None
kv.get("zzz", 5)    # -> None
```

Contract: `get` on an unknown key returns `None` and must not create an
entry. Timestamps are non-negative ints; keys and values are strings (an
empty string is a real value, not `None`).

Up to 200,000 operations: state the complexity of each method (`get` must
be O(log n)). Run the provided tests: `pytest temporal_kv -q`. Later parts
come with their own test files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

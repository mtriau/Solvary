# TTL Cache: Part 3

The same `TTLCache` grows. The last Netflix question was a cap: "memory is
bounded, so at most `k` entries, evicting the least recently used. How do TTL
and LRU interact?" Your earlier tests still run, and the Part 3 tests probe
exactly the interaction cases.

### What to implement

- `TTLCache(capacity: int | None = None)`: at most `capacity` **live** entries.
  `None` means unbounded. `capacity <= 0` raises `ValueError`.
- `evictions() -> int`: the total number of LRU evictions so far.
- `keys(now: int) -> list[str]`: live keys from least to most recently used.

### Rules

- When a `put` of a **new** key would exceed the capacity, first remove expired
  entries (run your Part 2 cleanup, the cheapest way to free space). Only if the
  cache is still full, evict the least recently used live entry.
- `get` of a live entry counts as a use. `put`, new or overwrite, also counts as a
  use and makes the key the most recently used.
- A `get` miss changes no recency.
- `put` on an existing live key is not a new entry and never evicts anything.
  A key whose entry has expired counts as new again.
- Expired entries are never "recently used": an entry that was read often but has
  expired is still removed, and it does not count as an eviction.
- `evictions()` counts only LRU evictions, not expiries and not deletes.
- `size` and `keys` report live entries only.

### Worked example

```python
c = TTLCache(capacity=2)
c.put("a", 1, ttl=1000, now=0)
c.put("b", 2, ttl=1000, now=0)
c.get("a", 1)                    # -> 1   (a is now more recent than b)
c.put("c", 3, ttl=5, now=2)      # full: nothing expired, so evict LRU = b
c.keys(2)                        # -> ["a", "c"]
c.evictions()                    # -> 1
c.put("d", 4, ttl=1000, now=7)   # c expired at 7: cleaned up, no LRU eviction
c.keys(7)                        # -> ["a", "d"]
c.evictions()                    # -> 1
```

### Clarifications

- **Expired before LRU?** Yes. Free space with cleanup first; evict by recency only if still full.
- **Does overwriting refresh recency?** Yes, and it never evicts, even at capacity.
- **Does a stale heap record affect capacity?** No. Only live entries count.
- **Does a failed `get` or a delete count as use?** No.
- **What is the cost of an eviction?** O(1) with an ordered dict.
- **Is `keys` order stable for ties?** There are no ties: every use is a distinct step.

Run the provided tests with **Submit**.

---
Interviewer notes

The interaction to hear is "expiry beats recency": clean up first so an expired-but-hot entry is never kept at the expense of a live one, and only then evict the LRU. An `OrderedDict` with `move_to_end` gives O(1) recency, next to the heap from Part 2; check that overwrites never evict and that stale records do not inflate the count. Verbal follow-ups: thread safety (every `get` mutates recency, so a read-write lock does not help; one lock around the dict and heap), a cleanup thread, and a timing wheel for very bursty expiries. Budget about 25 minutes.

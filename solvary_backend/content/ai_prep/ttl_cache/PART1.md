# TTL Cache: Part 1

Netflix asks this as a 60-minute IC5 phone screen: an in-memory key-value store
where every entry expires. The first-hand candidate had working code and was
still rejected, for code that was not concise and reasoning that was not
coherent, so the point here is a small, clean data model you can explain out
loud. `get` is the hot path, so keep it cheap. Later parts remove expired
entries without scanning and then add a size cap with LRU eviction.

### What to implement

In `ttl_cache.py`:

- `TTLCache(capacity: int | None = None)`. The capacity is ignored until Part 3.
- `put(key: str, value, ttl: int, now: int) -> None`
- `get(key: str, now: int)`: the value, or `None` if the key is missing or expired.
- `delete(key: str, now: int) -> bool`
- `size(now: int) -> int`: the number of **live** entries.

### Rules

- Time is an explicit integer `now` on every call (the unit does not matter).
  `now` never decreases across calls, and you may rely on that.
- An entry put at `now` with `ttl` is alive for the half-open interval
  `[now, now + ttl)`. At exactly `now + ttl` it is gone.
- `ttl <= 0` raises `ValueError`. So does a `None` value, which keeps
  `get` returning `None` unambiguous. Other falsy values (`0`, `""`, `False`)
  are fine.
- `put` on an existing key replaces the value **and** the TTL. The old expiry
  is forgotten entirely, even if it was later than the new one.
- `get` of an expired entry returns `None` and removes it.
- `delete` returns `True` only if a **live** entry was removed. Deleting an
  expired entry returns `False` (and removes it); a missing key returns `False`.
- `size` ignores expired entries even if they have not been physically removed.

### Worked example

```python
c = TTLCache()
c.put("a", 1, ttl=10, now=0)
c.get("a", 9)       # -> 1
c.get("a", 10)      # -> None   (expired exactly at now + ttl)

c.put("k", "x", ttl=100, now=0)
c.put("k", "y", ttl=5, now=1)    # the longer expiry is forgotten
c.get("k", 6)       # -> None
c.delete("k", 6)    # -> False  (nothing live to delete)
c.size(6)           # -> 0
```

### Clarifications

- **Is the boundary inclusive?** No. Alive at `now + ttl - 1`, gone at `now + ttl`.
- **Does an overwrite keep the old TTL?** No. Both value and TTL are replaced,
  whether the new TTL is shorter or longer.
- **Can a value be `None`?** No, that raises `ValueError`.
- **Can an expired key be put again?** Yes, it simply becomes a fresh entry.
- **What if `now` goes backwards?** It will not; you may assume it never does.
- **Do I need a background thread?** No. Expiry is judged from the `now` you are given.

Run the provided tests with **Submit**.

---
Interviewer notes

A dict of `key -> (value, expires_at)` with an `expires_at <= now` check on read is the whole answer; listen for the half-open boundary and for overwrites replacing the TTL, since the rejected candidate was loose on both. Push for a small data model the candidate can explain in one breath, and ask why `get` is lazy about expiry. Part 1 should take about 15 minutes.

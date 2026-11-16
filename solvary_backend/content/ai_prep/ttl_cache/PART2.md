# TTL Cache: Part 2

The same `TTLCache` grows. Netflix's next question was: "expired entries that
nobody reads just sit in memory, so how do you remove them without scanning
the whole cache?" A scan per cleanup is O(n); the answer is a structure that
hands you the soonest expiry first. Your Part 1 tests still run.

### What to implement

- `cleanup(now: int) -> int`: remove every expired entry and return how many
  were removed. It must cost O(k log n) for k expired entries, never a full scan.
- `expiring_before(t: int, now: int) -> list[str]`: the keys of **live** entries
  whose expiry is `< t`, sorted by expiry and then by key. This is how the tests
  look at your structure.

### Rules

- An entry is expired when `expiry <= now` (same half-open rule as Part 1).
- A min-heap of `(expires_at, key)` is the usual structure. Its trap is **stale
  records**: overwriting a key pushes a new record but cannot cheaply remove the
  old one, and deleting a key leaves its record behind. When an old record
  pops, it must not remove a key that was re-put with a later expiry, and it
  must not be counted if the key is already gone.
- Two standard fixes: give every entry a **version stamp** stored in both the
  entry and the heap record (a popped record counts only if the versions match),
  or on pop re-check that the entry's real expiry equals the record's.
- An entry already removed by `get`, `delete` or `size` is not counted again.
- `cleanup` removes only what is expired at `now`. Nothing live is ever removed.
- Performance matters: one test makes 200,000 puts and then 1,000 `cleanup`
  calls, and another overwrites the same 10 keys 100,000 times (so the heap
  holds many stale records) and still must be fast and leave all 10 live.

### Worked example

```python
c = TTLCache()
c.put("a", 1, ttl=5, now=0)
c.put("b", 1, ttl=20, now=0)
c.put("a", 2, ttl=50, now=1)      # leaves a stale record (expiry 5) in the heap
c.cleanup(10)                     # -> 0   (a's old record pops, is stale, is skipped)
c.expiring_before(30, 10)         # -> ["b"]
c.expiring_before(60, 10)         # -> ["b", "a"]
c.cleanup(20)                     # -> 1   (b)
c.delete("a", 21)                 # -> True
c.cleanup(100)                    # -> 0   (a's record is stale, a is gone)
```

### Clarifications

- **May `cleanup` scan the dict?** No. The tests time it against a scan.
- **Is a stale record "removed" work?** It is amortised: each record is pushed
  once and popped once, so skipping stale ones is fine, and nothing is counted for them.
- **Should I compact the heap?** Not required.
- **Does `expiring_before` include expired entries that are not cleaned yet?** No.
  Only live entries, i.e. `now < expiry < t`.
- **Does `cleanup` need to run before `get`?** No. `get` must stay correct on its own.
- **Is `now` ever less than a previous call?** No.

Run the provided tests with **Submit**.

---
Interviewer notes

Heap plus stale records is the whole part: a candidate who pops a record and deletes the key without checking the version or the expiry has the classic bug, so ask what happens to a key re-put with a longer TTL. Cost is O(log n) per put and amortised O(log n) per record removed; stale records inflate the heap but never the answer. Verbal follow-ups: a million keys expiring in the same second (bucket by second, a timing wheel, or bounded work per call), and where a background cleanup thread and its lock would sit. Budget about 20 minutes.

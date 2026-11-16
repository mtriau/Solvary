# Rolling CSAT Tracker: Part 2

The same `CSATTracker` grows an `update`: a customer may change their score
shortly after submitting it, but only while the conversation is still inside
the window. The Part 1 tests still run alongside the new ones.

### What to implement

- `update(conversation_id: str, score: int, current_time: int) -> bool`:
  change the score of a recorded conversation. Returns `True` if the change
  was applied, `False` otherwise.

### Rules

1. The update applies only if the conversation is still active at
   `current_time` (`current_time - timestamp <= window_size`). Then the
   score is replaced and `update` returns `True`.
2. If the conversation has expired, or the id was never recorded, nothing
   changes and `update` returns `False`.
3. An invalid score (not an integer from 1 to 5) raises `ValueError`, and
   changes nothing.
4. The conversation keeps its **original timestamp** and its position in the
   window. Updating does not renew it: it still expires exactly when it would
   have.
5. Updating to the same score is allowed and returns `True`.
6. Averages after an update use the new score. An expired conversation is
   never resurrected by an update.
7. `current_time` is non-decreasing across all calls that take it,
   `update` included.

### Worked example

```python
t = CSATTracker(5)
t.record("a", 1, 10)
t.record("b", 3, 14)
t.get_average(15)        # -> 2.0
t.update("a", 5, 15)     # -> True   (15 - 10 == 5, still active)
t.get_average(15)        # -> 4.0
t.get_average(16)        # -> 3.0    ("a" keeps its timestamp 10 and expires)
t.update("a", 2, 16)     # -> False  (expired, no-op)
t.update("zzz", 2, 16)   # -> False  (unknown id)
```

### Clarifications

- **Does an update refresh the timestamp?** No. The original timestamp
  decides expiry.
- **Update of an expired conversation?** `False`, and the average does not
  change.
- **Update of an unknown id?** `False`.
- **Is the boundary inclusive here too?** Yes: active at exactly
  `timestamp + window_size`.
- **Invalid score for an unknown id?** Still `ValueError`; validate the score
  first.
- **Where is the running state that must be patched?** Whatever you keep for
  the average (a sum, a count) has to reflect the replaced score.

Run the provided tests with **Submit**; later parts come with their own test
files.

---
Interviewer notes

The point is consistency: the update must patch the running sum (subtract the
old score, add the new one) and must first apply expiry for `current_time`,
otherwise an expired conversation is treated as active. Keep a per-conversation
map from id to (timestamp, score); the deque entry does not move. Graders value
tests of your own for update-at-the-boundary, update-after-expiry and
update-then-expire.

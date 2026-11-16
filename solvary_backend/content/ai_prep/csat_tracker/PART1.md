# Rolling CSAT Tracker: Part 1

A support product collects a customer-satisfaction (CSAT) score after each
conversation, and a dashboard shows the average of the scores from the last
few minutes. This is Decagon's most-reported phone-screen problem: the
45-minute CoderPad screen opens with this stateful class, expected in about
30 minutes, followed by a second short counting problem. The first-hand
candidate who passed it caught two of their own bugs while testing. Say your
data model out loud, and the time and space cost of each method, before you
write code.

### What to implement

Module `csat_tracker`, class `CSATTracker`:

- `CSATTracker(window_size: int)`: `window_size >= 0`, in the same units as
  the timestamps.
- `record(conversation_id: str, score: int, timestamp: int) -> None`: store
  one conversation's score.
- `get_average(current_time: int) -> float`: the mean score of the active
  conversations at `current_time`, rounded to 2 decimal places with Python's
  `round`.

### Rules

1. Scores are integers from 1 to 5. Anything else (including `0`, `6`,
   floats, strings) makes `record` raise `ValueError`.
2. Timestamps passed to `record` are strictly increasing across calls. A
   timestamp less than or equal to the previous recorded one raises
   `ValueError`.
3. A conversation id is recorded at most once, ever. A repeat raises
   `ValueError`, even if the first record has expired.
4. A call that raises must not change anything.
5. A conversation is **active** at `current_time` iff
   `current_time - timestamp <= window_size` (the boundary is inclusive).
6. `get_average` returns `0.0` when nothing is active.
7. `current_time` never decreases from one `get_*` call to the next and is
   never earlier than the latest recorded timestamp, so once a conversation
   expires it stays expired.

### Worked example

```python
t = CSATTracker(5)
t.record("a", 4, 10)
t.record("b", 5, 12)
t.get_average(12)   # -> 4.5
t.get_average(15)   # -> 4.5   (15 - 10 == 5, "a" is still active)
t.get_average(16)   # -> 5.0   (16 - 10 == 6, "a" expired)
t.get_average(18)   # -> 0.0   (18 - 12 == 6, nothing active)
t.record("a", 3, 20)   # raises ValueError (id already used)
```

### Clarifications

- **Is a score recorded at t=10 with window 5 active at 15?** Yes. At 16 it
  is not.
- **Rounding?** `round(mean, 2)`: scores 4, 4, 5 give `4.33`.
- **Nothing active?** `0.0`, not an error.
- **Can `current_time` go backwards?** No, so expiry never has to be undone.
- **Can a recorded timestamp equal an earlier one?** No; it raises.
- **May an expired id be recorded again?** No; ids are unique forever.
- **Performance?** Up to 2e5 operations and a window up to 1e9, so avoid
  rescanning every conversation on each query.

Run the provided tests with **Submit**; later parts come with their own test
files.

---
Interviewer notes

Expected design: a deque of (timestamp, id) popped from the left as
conversations expire, plus a running sum and count, so `get_average` is
amortised O(1). The inclusive boundary (`<=`, not `<`) is the classic bug,
and so is forgetting that an id stays used after it expires. Graders value
you writing your own edge-case tests (boundary, empty, window of 0) before
being asked.

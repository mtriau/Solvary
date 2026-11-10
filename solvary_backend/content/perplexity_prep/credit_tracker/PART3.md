# Credit Tracker: Part 3 (reveal verbatim)

Interviewer: after Part 2 is green, read the block below to the candidate, then
copy `_interviewer/tests/credit_tracker/test_credit_tracker_p3.py` into
`credit_tracker/` and have them run `pytest credit_tracker -q`. Keep the
Part 1 and Part 2 files in place: the same class must stay green on all
three.

---

Part 3: out-of-order events.

- Calls may now arrive in ANY time order.
- `check_credit(t)` returns the balance at `t` computed by applying every
  event with timestamp <= t in timestamp order (ties: insertion order).
  An add is an event at its `start`.
- If during that replay any subtraction at or before `t` could not be
  fully covered, `check_credit(t)` returns -1.
- `subtract_credit` now just records the event; its return value is no
  longer meaningful for an out-of-order call (return 0 for those; state
  it). The Part 2 tests still run, so a subtraction that arrives in time
  order must still return what it spent.
- `check_credit(t)` for a `t` before any event returns 0.
- Scale: the tests record 20,000 adds and 5,000 subtractions in random
  time order and then run 200 checks; the whole thing must finish in under
  5 seconds.

---

Interviewer notes (do not read aloud):
- Expected shape: event list kept sorted by (ts, insertion_idx) via
  `bisect.insort` (or sorted on demand); `check` replays with the Part 2
  heap logic into fresh state. O(n log n) per check; acceptable (the scale
  test allows it: 200 replays of 25K events is about 1 second). Discuss,
  don't build: snapshots every k events, or invalidating a cached replay
  only when an event older than the cache arrives.
- What the scale test kills: replaying on every subtract (5,000 replays),
  or re-sorting the whole event list on every add.
- Watch: the replay must include adds whose start <= t but whose end < t
  (they contribute 0 at t but may have covered an earlier subtraction):
  `test_grant_that_expired_before_t_is_still_replayed_for_earlier_subtractions`.
- Probes: `test_subtract_recorded_before_its_covering_add_is_short_until_the_add_arrives`
  (-1 then 30), `test_subtraction_after_a_grant_expired_is_short_only_for_checks_at_or_after_it`
  (check(10) fine, check(11) == -1), same-timestamp add-then-sub covered
  vs sub-then-add -1.

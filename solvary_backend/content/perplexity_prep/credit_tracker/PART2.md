# Credit Tracker: Part 2 (reveal verbatim)

Interviewer: after Part 1 is green, read the block below to the candidate, then
copy `_interviewer/tests/credit_tracker/test_credit_tracker_p2.py` into
`credit_tracker/` and have them run `pytest credit_tracker -q`.

---

Part 2: subtract.

- `subtract_credit(t: int, amount: int) -> int`: spend `amount` from the
  grants active at time `t`, drawing from the grant with the EARLIEST end
  time first (ties: the one added first). If the active total is less than
  `amount`, spend everything available. Return the amount actually spent.
  Spent credit is gone for all later times.
- In this part, calls arrive in non-decreasing time order (`start` for
  add_credit, `t` for subtract/check).
- Boundaries are inclusive: a subtraction exactly at a grant's `end` (or
  exactly at its `start`) can draw from it. Subtracting when nothing is
  active returns 0.

Examples (give on request):
  add(1,10,100); add(5,7,50); subtract(6, 70) -> 70 (50 from the 5..7
  grant, 20 from the 1..10 grant); check(6) -> 80; check(8) -> 80;
  subtract(8, 500) -> 80; subtract(9, 1) -> 0.

---

Interviewer notes (do not read aloud):
- The split-by-expiry probe is `test_subtract_draws_from_earliest_expiring_grant_first`:
  check(8) == 80 proves the 1..10 grant was only charged 20.
- Expected shape: each grant has `remaining`; a min-heap of
  `(end, insertion_idx, grant)`; on subtract, lazily pop grants with
  `end < t` (gone forever since time only moves forward), then peel from
  the top. Also fine: sort active grants by (end, idx) per call; ask them
  to improve if quick.
- Make them say why no grant in the structure can have start > t (adds are
  ordered by start).
- The tie rule (same end: first added first) is not observable through
  check_credit, since tied grants expire together; the suite only checks
  the totals. Ask them to state the rule anyway.
- The suite never calls check_credit after a short subtraction (Part 3
  changes what that returns). Do not point this out.

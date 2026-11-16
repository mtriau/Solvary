# Rolling CSAT Tracker: Part 3

The same `CSATTracker` grows percentiles. The dashboard wants the median
score (p50) and the 90th percentile, plus a count per score. The Part 1 and
Part 2 tests still run alongside the new ones.

### What to implement

- `get_percentile(current_time: int, p: int | float) -> int | None`: the
  score at percentile `p` among the active conversations.
- `get_distribution(current_time: int) -> dict[int, int]`: how many active
  conversations have each score.

### Rules

1. Sort the active scores ascending; with `n` of them, the answer is the
   element at index `ceil(p / 100 * n) - 1`, clamped to `[0, n - 1]`
   (nearest-rank). So `p = 0` gives the minimum and `p = 100` the maximum.
2. `p` must satisfy `0 <= p <= 100`, otherwise `ValueError`. `p` may be a
   float.
3. If nothing is active, `get_percentile` returns `None`.
4. `get_distribution` always returns all five keys `1..5`, with `0` for
   scores nobody has.
5. Both methods apply expiry for `current_time` like `get_average`, and they
   must reflect every `update`.
6. Performance: up to 2e5 operations. A test does 200,000 records with
   interleaved queries and must finish well under 2 seconds, so an O(n) scan
   or sort per query is too slow.

### Worked example

```python
t = CSATTracker(1000)
for i, s in enumerate([5, 1, 4, 2], start=1):
    t.record(f"c{i}", s, i)          # sorted: 1 2 4 5
t.get_percentile(4, 50)              # -> 2    (index ceil(2.0) - 1 = 1)
t.get_percentile(4, 100)             # -> 5
t.get_percentile(4, 0)               # -> 1
t.get_distribution(4)                # -> {1: 1, 2: 1, 3: 0, 4: 1, 5: 1}
t.update("c4", 5, 5)                 # -> True  (the 2 becomes a 5)
t.get_distribution(5)                # -> {1: 1, 2: 0, 3: 0, 4: 1, 5: 2}
CSATTracker(10).get_percentile(1, 50)  # -> None
```

### Clarifications

- **Is p50 of four scores the 2nd or 3rd smallest?** The 2nd: index
  `ceil(0.5 * 4) - 1 = 1`.
- **No interpolation?** Right. The result is always one of the actual scores.
- **Nothing active?** `None` for the percentile; a dictionary of five zeros
  for the distribution.
- **`p` outside 0..100?** `ValueError`.
- **Why a histogram?** There are only five possible scores. Keeping a count
  per score makes the average O(1) after expiry and a percentile a walk over
  five buckets, with no sorting. The hard part is keeping every mutation
  consistent with it: expiry decrements the bucket of the expiring score, and
  an update moves one count from the old bucket to the new one.
- **Float `p`?** Compute `p * n / 100` if you want integer `p` to stay exact.

Run the provided tests with **Submit**.

---
Interviewer notes

The strong answer is the five-bucket histogram next to the deque and map:
expiry pops the deque and decrements the popped conversation's current bucket
(read from the map, since an update may have changed it), and an update moves
one count between buckets. Graders look for the nearest-rank index done
carefully (off-by-one, clamping, empty case) and for you testing percentile
results after an update and after expiry yourself.

### Why this is idiomatic

- `groupby` groups *consecutive* equal elements, which is precisely a run. People remember it as "like SQL GROUP BY" and get burned; it only groups adjacent items, and that is the behaviour you want here.
- Each group is a lazy iterator shared with the outer iteration, so you must consume it before moving on. `sum(1 for _ in group)` counts without building a list; `len(list(group))` is also fine.
- The hand-rolled loop needs a "previous character" variable, a counter and a final flush after the loop. That flush is the classic off-by-one bug; `groupby` has no such step.

### The habit

"Consecutive runs of equal things" is `itertools.groupby`.

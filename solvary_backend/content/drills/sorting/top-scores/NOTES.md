### Why this is idiomatic

- Iterating a dict yields its keys, so `sorted(scores, key=...)` sorts the names directly.
- Negating the score in the key gives "highest first" while the name tie-break stays ascending. `reverse=True` would reverse the name order too, which is wrong here.
- Slicing `[:n]` is safe for `n` larger than the list and for `n == 0`.
- For huge inputs and small `n`, `heapq.nsmallest(n, scores, key=...)` with the same key avoids a full sort. Mention it; do not reach for it first.

### The habit

Descending on one field and ascending on another: negate the numeric field in the key instead of `reverse=True`.

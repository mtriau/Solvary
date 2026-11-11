### Why this is idiomatic

- The dict is the whole trick: one pass, O(n), and the question "have I seen the complement?" is a single `.get`.
- Check before you store. If you store `x` first and then look up `target - x`, `[4, 1]` with target 8 finds itself.
- `seen.setdefault(x, j)` keeps the earliest index for a repeated value, which is what "smallest `j`" needs when the complement equals `x`.
- The walrus `(i := seen.get(...)) is not None` looks up once and tests once. Compare with `if target - x in seen: return seen[target - x], j`, which hashes twice. Both are fine; know both.

### The habit

"Find a pair that satisfies something" is almost always a dict or set keyed by what you would need the partner to be. Nested `for i ... for j in range(i + 1, ...)` is the answer you give only after saying "the quadratic way is obvious, here is the linear one".

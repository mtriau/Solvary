### Why this is idiomatic

- Python's `%` always returns a non-negative result for a positive divisor, so `k %= len(items)` turns any `k`, including negative and oversized, into a valid left rotation. No `if k < 0` branch.
- `items[k:] + items[:k]` says "the part after the cut, then the part before" and builds a new list in one expression.
- The empty-list guard exists only because `% 0` is undefined. Guards like this are fine when they are one obvious line.
- `collections.deque` has a `rotate` method for in-place rotation of a queue; here the spec asks for a new list, so slicing is the better fit.

### The habit

Use `%` to wrap indices instead of writing sign-dependent branches.

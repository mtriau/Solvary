### Why this is idiomatic

- `range(0, len(items), size)` produces the start index of every chunk, and the slice `items[i:i + size]` never over-runs, so the short last chunk needs no special handling.
- Validation up front with a specific exception and a message that includes the bad value. Checking `size < 1` once is better than letting `range` raise a confusing `ValueError: range() arg 3 must not be zero`.
- Python 3.12 has `itertools.batched(items, size)`, which returns tuples. Know it exists; the comprehension is still the portable, readable version.

### The habit

Validate arguments at the top of the function, then write the happy path as one expression.

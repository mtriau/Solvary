### Why this is idiomatic

- `enumerate` hands you the index and the item together. `for i in range(len(lines))` followed by `lines[i]` is the C way, and it does not work on iterators at all (the suite passes one).
- `start=1` moves the numbering without `i + 1` scattered through the body.
- f-string, comprehension: the same two habits as before, applied again.

### The habit

If you need the index while looping, it is `enumerate`. If you don't need it, don't ask for it.

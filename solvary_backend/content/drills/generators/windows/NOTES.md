### Why this is idiomatic

- `zip(items, items[1:])` is the classic way to walk adjacent pairs; it stops when the shorter (shifted) slice runs out, which handles the end of the list for free.
- The general form shifts by `0, 1, ..., size - 1` and zips the slices with `*` to unpack them as arguments. `zip` truncating to the shortest means a too-short input yields nothing, matching the spec.
- The index-arithmetic version, `[tuple(items[i:i + size]) for i in range(len(items) - size + 1)]`, is also idiomatic and arguably clearer for large `size`. Both are fine; the thing to avoid is a `while` loop with manual bounds.
- For `size == 2`, `itertools.pairwise(items)` (3.10+) is the named version.

### The habit

Adjacent elements are `zip(xs, xs[1:])` or `pairwise`, not `xs[i]` and `xs[i + 1]` inside a `range(len(xs) - 1)` loop.

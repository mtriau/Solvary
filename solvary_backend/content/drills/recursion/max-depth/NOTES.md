### Why this is idiomatic

- `max(iterable, default=0)` is the detail that makes this a one-liner. Without `default`, `max` of an empty generator raises, and you need an explicit `if not sublists: return 1`.
- The generator filters with `if isinstance(x, list)`, so non-list elements neither recurse nor count. Checking for `list` specifically (not any iterable) is deliberate: strings are iterable and would recurse forever.
- "1 + max of the children" is the shape of every tree-depth function. Binary tree height is `1 + max(height(left), height(right))` with `height(None) == 0`.
- Depth here is bounded by the recursion limit, like any recursive tree walk. For data thousands of levels deep you would switch to an explicit stack of `(node, level)` pairs.

### The habit

`max(..., default=...)` and `min(..., default=...)` whenever the iterable might be empty. Recursive "height" is always one plus the max over children.

### Why this is idiomatic

- `defaultdict(list)` creates the list the first time a key is seen, so the loop body is one line. The alternatives, `setdefault(len(word), []).append(word)` or an `if key not in groups` check, say the same thing less directly.
- `dict(groups)` at the end hands callers an ordinary dict. A `defaultdict` that escapes a function silently creates entries on lookup, which surprises people; converting is a small courtesy.
- The grouping loop is the right shape: comprehension tricks for grouping get unreadable fast.

### The habit

Group with `defaultdict(list)`, return a `dict`.

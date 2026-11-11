### Why this is idiomatic

- The recursion carries the one piece of state that changes as you descend: the path. Passing it as a parameter with a default (`prefix=""`) keeps the public signature clean and makes the top-level call `flatten(d)`.
- `f"{prefix}.{key}" if prefix else key` avoids a leading dot without a special-case branch for depth zero.
- `isinstance(value, dict)` is the one decision: recurse or record. Lists are deliberately leaves here; say so, because the interviewer may ask about them next.
- `out.update(flatten(...))` merges the child's results. The generator version replaces `out` with `yield path, value` and `yield from flatten(value, path)`, then `dict(flatten(d))` at the call site. Same recursion, less bookkeeping.

### The habit

Recursive structure, recursive function. Identify the state that grows with depth (here the path) and pass it down; identify the base decision (leaf or not) and make it the only `if`.

### Why this is idiomatic

- `zip` walks two sequences in lock-step and stops at the shorter one, which is exactly the truncation rule. Indexing with `range(min(len(a), len(b)))` says the same thing with three function calls.
- `dict(pairs)` accepts any iterable of 2-tuples, so `dict(zip(...))` is the canonical way to build a mapping from parallel sequences.
- When unequal lengths should be an error rather than a truncation, `zip(names, scores, strict=True)` raises. Know both.

### The habit

Parallel sequences are iterated with `zip`, never with a shared index.

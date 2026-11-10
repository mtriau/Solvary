### Why this is idiomatic

- `all(cond for x in xs)` and `any(cond for x in xs)` read like the sentence in the spec. A loop with a flag variable and a `break` is the hand-rolled version of exactly these two functions.
- Both short-circuit: `all` stops at the first false, `any` at the first true. The suite checks that with a generator that fails if read too far.
- They return `True`/`False` (the suite uses `is`), and `all([])` is `True`, `any([])` is `False`, matching the mathematical convention; no empty-list guard.
- Note the two functions are negations of each other: `any_failed == not all_passed`. Either definition is fine; the generator form stays readable in both.

### The habit

A loop whose only job is to set a boolean flag is `any` or `all`.

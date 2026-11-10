### Why this is idiomatic

- `sorted(...)` returns a new list; `people.sort()` would reorder the caller's list in place. The spec says "leave the input unchanged", so `sorted` is the only correct choice.
- A tuple key `(age, name)` sorts by age and breaks ties by name, because tuples compare element by element. No `cmp_to_key`, no sorting twice.
- When a key just pulls fields out, `operator.itemgetter("age", "name")` is an equally idiomatic alternative to the lambda.

### The habit

One `sorted` call with a tuple key handles every "sort by X, then by Y" requirement.

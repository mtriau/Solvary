### Why this is idiomatic

- The nested comprehension reads in the same order as the nested `for` loops it replaces: `for row in rows` first, then `for x in row`. People get this backwards once, then never again.
- `itertools.chain.from_iterable(rows)` is the other idiomatic answer, especially when `rows` is a lazy iterable. `sum(rows, [])` is not: it is quadratic and reads as a trick.
- The result is a new list; the input rows are untouched.

### The habit

Two nested loops whose body is one `append` are one comprehension with two `for` clauses.

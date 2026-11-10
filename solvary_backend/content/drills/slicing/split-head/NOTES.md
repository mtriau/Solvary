### Why this is idiomatic

- `first, *rest = items` is the Python spelling of head/tail. It works on any iterable, `rest` is always a fresh list, and an empty input raises `ValueError: not enough values to unpack`, which is the exact exception the spec asks for. Three requirements, zero `if` statements.
- `items[0], items[1:]` would also work on lists but fails on iterators and needs an explicit empty check to produce `ValueError` rather than `IndexError`.
- Returning a tuple is just `return first, rest`; the parentheses are optional and usually omitted.

### The habit

Use star-unpacking for head/tail and "everything except the last" (`*init, last = items`) instead of index arithmetic.

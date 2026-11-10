### Why this is idiomatic

- `first, *rest = name.split("_")` takes the head and the tail in one line. `split` on an empty string gives `[""]`, so `first` is `""` and `rest` is empty, and the empty input works without a special case.
- `"".join(word.capitalize() for word in rest)` builds the suffix from a generator expression; `join` is the way to concatenate many strings, never `+=` in a loop.
- `capitalize()` upper-cases the first character and lower-cases the rest, which is what camelCase wants for lower-case input.

### The habit

Build strings with `join` over an iterable of pieces. The `+=` loop is quadratic in the worst case and reads as C.

# Infinite evens

Write `evens()` that yields `0, 2, 4, 6, ...` forever. Callers take as many as they need with `itertools.islice` or `next`.

### Signature

`def evens()`

### Examples

```python
from itertools import islice
list(islice(evens(), 5)) == [0, 2, 4, 6, 8]
next(evens()) == 0
```

### Idiom

A generator function with `yield` in an infinite loop (or `itertools.count(0, 2)`).

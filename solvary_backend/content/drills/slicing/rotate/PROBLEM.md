# Rotate a list

Rotate a list left by `k` positions and return a new list. `k` may be larger than the list or negative (a negative `k` rotates right). The input must not change.

### Signature

`def rotate(items: list, k: int) -> list`

### Examples

```python
rotate([1, 2, 3, 4, 5], 2) == [3, 4, 5, 1, 2]
rotate([1, 2, 3], -1) == [3, 1, 2]
rotate([1, 2, 3], 7) == [2, 3, 1]
rotate([], 3) == []
```

### Idiom

Normalise `k` with `%`, then concatenate two slices.

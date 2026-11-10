# Flatten one level

Flatten a list of lists into a single list, keeping the order.

### Signature

`def flatten(rows: list[list[int]]) -> list[int]`

### Examples

```python
flatten([[1, 2], [3], [], [4, 5]]) == [1, 2, 3, 4, 5]
flatten([]) == []
```

### Idiom

A nested comprehension: `for row in rows for x in row`, in that order (outer loop first).

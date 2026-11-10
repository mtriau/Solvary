# Chunk a list

Split a list into consecutive chunks of `size` elements. The last chunk may be shorter. A `size` below 1 is an error: raise `ValueError`.

### Signature

`def chunk(items: list, size: int) -> list[list]`

### Examples

```python
chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
chunk([], 3) == []
chunk([1], 0)      # raises ValueError
```

### Idiom

A comprehension over `range(0, len(items), size)` that slices `items[i:i + size]`.

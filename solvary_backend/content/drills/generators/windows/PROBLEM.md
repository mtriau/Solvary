# Sliding windows

Return every window of `size` consecutive elements as a tuple. If the list is shorter than `size`, return an empty list.

### Signature

`def windows(items: list, size: int) -> list[tuple]`

### Examples

```python
windows([1, 2, 3, 4], 2) == [(1, 2), (2, 3), (3, 4)]
windows([1, 2, 3, 4], 3) == [(1, 2, 3), (2, 3, 4)]
windows([1, 2], 3) == []
```

### Idiom

`zip` over shifted slices: `zip(items, items[1:])` for pairs, `zip(*(items[i:] for i in range(size)))` in general. For `size == 2` there is also `itertools.pairwise`.

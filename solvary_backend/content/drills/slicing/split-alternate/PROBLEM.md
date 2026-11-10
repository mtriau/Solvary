# Alternate positions

Split a list into the elements at even positions and the elements at odd positions (0-based).

### Signature

`def split_alternate(items: list) -> tuple[list, list]`

### Examples

```python
split_alternate([10, 11, 12, 13, 14]) == ([10, 12, 14], [11, 13])
split_alternate([]) == ([], [])
```

### Idiom

Extended slices: `items[::2]` and `items[1::2]`.

# Head and tail

Split a list into its first element and the rest. An empty list is an error: raise `ValueError`.

### Signature

`def split_head(items: list) -> tuple[object, list]`

### Examples

```python
split_head([1, 2, 3]) == (1, [2, 3])
split_head(["only"]) == ("only", [])
split_head([])        # raises ValueError
```

### Idiom

Star-unpacking: `first, *rest = items`. The `ValueError` on an empty list comes for free.

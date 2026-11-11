# Depth of a nested list

Return the nesting depth of `nested`: a flat list (or an empty one) has depth 1, and each level of list-in-list adds one. Non-list elements do not add depth.

### Signature

`def depth(nested: list) -> int`

### Examples

```python
depth([]) == 1
depth([1, 2]) == 1
depth([1, [2, [3]], [4]]) == 3
```

### Idiom

`1 + max((depth(x) for x in nested if isinstance(x, list)), default=0)`. The `default=0` handles a list with no sub-lists, so there is no separate base case.

# Invert a dict

Swap keys and values. Values are guaranteed unique.

### Signature

`def invert(mapping: dict[str, int]) -> dict[int, str]`

### Examples

```python
invert({"a": 1, "b": 2}) == {1: "a", 2: "b"}
invert({}) == {}
```

### Idiom

A dict comprehension over `.items()`.

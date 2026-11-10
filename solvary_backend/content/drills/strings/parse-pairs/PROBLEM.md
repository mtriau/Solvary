# Parse key=value pairs

Parse a string of `key=value` pairs separated by semicolons into a dict with integer values. Whitespace around keys and values is ignored, and empty items (from stray semicolons) are skipped.

### Signature

`def parse_pairs(text: str) -> dict[str, int]`

### Examples

```python
parse_pairs("a=1;b=22;c=3") == {"a": 1, "b": 22, "c": 3}
parse_pairs(" a = 1 ; b=2 ") == {"a": 1, "b": 2}
parse_pairs("a=1;;b=2;") == {"a": 1, "b": 2}
parse_pairs("") == {}
```

### Idiom

`str.split` for the items, `str.partition` for the key and value, `str.strip` on both.

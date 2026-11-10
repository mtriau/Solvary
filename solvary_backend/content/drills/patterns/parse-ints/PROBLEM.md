# Parse a list of numbers

Parse integers from text, one per line. Blank lines and comment lines (first non-space character is `#`) are ignored, and surrounding whitespace is stripped.

### Signature

`def parse_ints(text: str) -> list[int]`

### Examples

```python
parse_ints("1\n  2 \n\n# three\n-4\n") == [1, 2, -4]
parse_ints("") == []
```

### Idiom

`splitlines()`, a comprehension, and the walrus `:=` to strip once and reuse the stripped line in the filter.

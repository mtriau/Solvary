# Number the lines

Prefix every line with its 1-based number and a colon.

### Signature

`def number_lines(lines: list[str]) -> list[str]`

### Examples

```python
number_lines(["alpha", "beta"]) == ["1: alpha", "2: beta"]
number_lines([]) == []
```

### Idiom

`enumerate(lines, start=1)`. No manual counter, no `range(len(...))`.

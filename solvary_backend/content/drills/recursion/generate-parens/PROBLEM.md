# Generate balanced parentheses

Return every string of `n` pairs of balanced parentheses. Order does not matter.

### Signature

`def generate_parens(n: int) -> list[str]`

### Examples

```python
sorted(generate_parens(2)) == ["(())", "()()"]
generate_parens(0) == [""]
len(generate_parens(4)) == 14
```

### Idiom

Backtracking with two counters: `go(partial, opened, closed)`. You may add `(` while `opened < n`, and `)` while `closed < opened`. When `len(partial) == 2 * n`, record it. The constraints prune invalid prefixes so you never generate and filter.

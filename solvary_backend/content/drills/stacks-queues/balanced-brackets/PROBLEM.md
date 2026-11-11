# Balanced brackets

Return whether every bracket in `s` is closed by the matching bracket in the right order. Brackets are `()`, `[]`, `{}`; other characters are ignored.

### Signature

`def balanced(s: str) -> bool`

### Examples

```python
balanced("([]{})") is True
balanced("f(x[0]) + {y}") is True
balanced("(]") is False
balanced("((") is False
```

### Idiom

A list as a stack and a dict from closer to opener: `PAIRS = {")": "(", "]": "[", "}": "{"}`. Push openers; on a closer, pop and compare. Balanced means the stack is empty at the end: `return not stack`.

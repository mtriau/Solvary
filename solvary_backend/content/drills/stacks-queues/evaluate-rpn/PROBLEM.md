# Evaluate reverse Polish notation

Evaluate an expression in reverse Polish notation. Tokens are integers or one of `+ - * /`. Division truncates toward zero. The input is always valid.

### Signature

`def evaluate_rpn(tokens: list[str]) -> int`

### Examples

```python
evaluate_rpn(["2", "1", "+", "3", "*"]) == 9        # (2 + 1) * 3
evaluate_rpn(["4", "13", "5", "/", "+"]) == 6       # 4 + 13 / 5
evaluate_rpn(["7", "-3", "/"]) == -2                # truncates toward zero
```

### Idiom

A stack and a dict of operators to functions: `{"+": operator.add, "-": operator.sub, "*": operator.mul, "/": lambda a, b: int(a / b)}`. Pop the right operand first, then the left.

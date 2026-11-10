# Format a receipt

Format `(name, price)` items as fixed-width lines: the name left-aligned in 12 characters, the price right-aligned in 8 characters with two decimals. End with a `TOTAL` line in the same layout.

### Signature

`def format_receipt(items: list[tuple[str, float]]) -> list[str]`

### Examples

```python
format_receipt([("Coffee", 3.5), ("Bagel", 2.25)]) == [
    "Coffee          3.50",
    "Bagel           2.25",
    "TOTAL           5.75",
]
format_receipt([]) == ["TOTAL           0.00"]
```

Each line is exactly 20 characters.

### Idiom

f-strings with format specs: `{name:<12}` and `{price:>8.2f}`.

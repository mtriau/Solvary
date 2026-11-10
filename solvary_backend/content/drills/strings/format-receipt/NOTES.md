### Why this is idiomatic

- Format specs live inside the f-string: `<12` means left-align in 12 columns, `>8.2f` means right-align in 8 columns with two decimals. No `ljust`, `rjust`, `round` or `str()` calls.
- The item lines come from a comprehension that unpacks each tuple into `name, price` directly in the `for` clause.
- `sum(price for _, price in items)` reads the total straight off the data; `_` marks the value you ignore.
- A literal inside an f-string placeholder (`{'TOTAL':<12}`) is fine and keeps every line in the same shape.

### The habit

When you format numbers or align columns, write the format spec and let the f-string do the padding.

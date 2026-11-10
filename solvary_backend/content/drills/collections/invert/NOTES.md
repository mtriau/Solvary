### Why this is idiomatic

- Iterate dicts with `.items()` when you need both halves; unpack them in the `for` clause. `for key in mapping: ... mapping[key]` does a second lookup for nothing.
- The comprehension `{value: key ...}` states the inversion directly.
- Dicts keep insertion order, so the inverted dict follows the input's order with no extra work.

### The habit

`for key, value in mapping.items()`, never `for key in mapping.keys()` followed by `mapping[key]`.

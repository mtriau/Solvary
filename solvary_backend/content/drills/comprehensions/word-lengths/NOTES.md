### Why this is idiomatic

- `{key: value for item in iterable}` is the dict twin of the list comprehension. One expression, no `result = {}`, no `result[word] = ...`.
- Duplicate keys simply overwrite, which is exactly what a dict does; no special case needed.
- If you ever need `dict(zip(words, map(len, words)))`, the comprehension is still clearer.

### The habit

Any time you build a dict with a loop whose body is a single assignment, it is a dict comprehension.

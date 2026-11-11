# Flatten a nested dict with dotted keys

Turn nested dicts into a single-level dict whose keys are the paths joined with `.`. Leaves (non-dict values) keep their values; an empty nested dict contributes nothing.

### Signature

`def flatten(d: dict, prefix: str = "") -> dict[str, object]`

### Examples

```python
flatten({"a": {"b": 1, "c": {"d": 2}}, "e": 3}) == {"a.b": 1, "a.c.d": 2, "e": 3}
flatten({}) == {}
```

### Idiom

Recursion that carries the path built so far. For each `key, value`, compute `path = f"{prefix}.{key}" if prefix else key`; if `value` is a dict, `out.update(flatten(value, path))`, otherwise `out[path] = value`. A generator with `yield from` is the other shape.

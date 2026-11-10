# Merge settings

Combine default settings with user overrides. An override whose value is `None` means "not set" and must not replace the default. Neither input may be mutated.

### Signature

`def merge_settings(defaults: dict[str, object], overrides: dict[str, object]) -> dict[str, object]`

### Examples

```python
merge_settings({"theme": "light", "font": 12}, {"theme": "dark", "font": None})
# -> {"theme": "dark", "font": 12}
merge_settings({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}
```

### Idiom

The dict union operator `|` (or `{**a, **b}`) with a comprehension that drops the `None`s.

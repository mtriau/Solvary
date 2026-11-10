# Nested lookup

Fetch a value from nested dicts and lists by a path of keys and indexes. If any step is missing or the wrong type, return `default` instead of raising.

### Signature

`def dig(data, *path, default=None)`

### Examples

```python
cfg = {"db": {"hosts": ["a", "b"], "port": 5432}}
dig(cfg, "db", "port") == 5432
dig(cfg, "db", "hosts", 1) == "b"
dig(cfg, "db", "user") is None
dig(cfg, "db", "hosts", 9, default="?") == "?"
dig(cfg, "db", "port", "x") is None      # 5432 is not subscriptable
```

### Idiom

EAFP: try the lookups and catch `(KeyError, IndexError, TypeError)`, instead of checking types and keys before every step.

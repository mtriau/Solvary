# Sort version strings

Sort dotted version strings numerically, so that `1.10.0` comes after `1.9.0`. Shorter versions sort before longer ones with the same prefix (`1.2` before `1.2.1`).

### Signature

`def sort_versions(versions: list[str]) -> list[str]`

### Examples

```python
sort_versions(["1.10.0", "1.9.0", "1.2", "1.2.1"]) == ["1.2", "1.2.1", "1.9.0", "1.10.0"]
```

### Idiom

`sorted` with a key that turns each version into a tuple of ints.

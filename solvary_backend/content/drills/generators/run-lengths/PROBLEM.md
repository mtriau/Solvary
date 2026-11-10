# Run-length encoding

Encode a string as a list of `(character, run_length)` pairs for each maximal run of identical characters.

### Signature

`def run_lengths(text: str) -> list[tuple[str, int]]`

### Examples

```python
run_lengths("aaabcc") == [("a", 3), ("b", 1), ("c", 2)]
run_lengths("abab") == [("a", 1), ("b", 1), ("a", 1), ("b", 1)]
run_lengths("") == []
```

### Idiom

`itertools.groupby` with no key function; the group is an iterator, so its length is `len(list(group))` or `sum(1 for _ in group)`.

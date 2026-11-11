# Remove duplicates, keep order

Return the items of `items` with duplicates removed, keeping the first occurrence of each in its original position.

### Signature

`def dedupe(items: Iterable[Hashable]) -> list`

### Examples

```python
dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
dedupe("mississippi") == ["m", "i", "s", "p"]
dedupe([]) == []
```

### Idiom

`list(dict.fromkeys(items))`. Dicts are insertion-ordered, so a dict's keys are exactly "unique, first-seen order". Say it out loud in an interview: "dedupe preserving order is `dict.fromkeys`."

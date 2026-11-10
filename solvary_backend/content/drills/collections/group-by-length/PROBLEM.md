# Group words by length

Group words by their length. Each group keeps the words in their original order. Return a plain `dict` (a missing length must raise `KeyError`).

### Signature

`def group_by_length(words: list[str]) -> dict[int, list[str]]`

### Examples

```python
group_by_length(["cat", "horse", "dog", "ox"]) == {3: ["cat", "dog"], 5: ["horse"], 2: ["ox"]}
group_by_length([]) == {}
```

### Idiom

`collections.defaultdict(list)` while grouping, converted back to a `dict` on the way out.

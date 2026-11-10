# Top n scores

Return the names of the `n` highest scorers, highest first. Equal scores are ordered by name ascending.

### Signature

`def top_scores(scores: dict[str, int], n: int) -> list[str]`

### Examples

```python
top_scores({"ann": 90, "bob": 95, "cy": 90, "dee": 70}, 3) == ["bob", "ann", "cy"]
top_scores({}, 2) == []
```

### Idiom

One `sorted` with a key that negates the score: `(-score, name)`.

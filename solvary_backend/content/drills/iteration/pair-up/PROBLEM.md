# Pair names with scores

Build a dict from parallel lists of names and scores. If the lists differ in length, extra elements of the longer list are dropped.

### Signature

`def pair_up(names: list[str], scores: list[int]) -> dict[str, int]`

### Examples

```python
pair_up(["ann", "bob"], [90, 85]) == {"ann": 90, "bob": 85}
pair_up(["ann", "bob", "cy"], [1]) == {"ann": 1}
```

### Idiom

`dict(zip(names, scores))`.

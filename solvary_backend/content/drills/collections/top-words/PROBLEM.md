# Most common words

Return the `n` most common words in `text` with their counts, most common first. Words are separated by whitespace and compared case-insensitively (report them lower-case). Ties keep first-seen order.

### Signature

`def top_words(text: str, n: int) -> list[tuple[str, int]]`

### Examples

```python
top_words("the cat the dog The bird", 2) == [("the", 3), ("cat", 1)]
top_words("", 3) == []
```

### Idiom

`collections.Counter` and its `most_common`.

# Longest word

Return the longest word. On a tie, return the first of the longest. Return `None` for an empty list.

### Signature

`def longest_word(words: list[str]) -> str | None`

### Examples

```python
longest_word(["a", "bbb", "cc"]) == "bbb"
longest_word(["aa", "bb"]) == "aa"
longest_word([]) is None
```

### Idiom

`max` with `key=len` and `default=None`. No sorting.

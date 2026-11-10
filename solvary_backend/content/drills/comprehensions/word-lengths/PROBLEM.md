# Word lengths

Build a dictionary that maps each word to its length.

### Signature

`def word_lengths(words: list[str]) -> dict[str, int]`

### Examples

```python
word_lengths(["hi", "hello"]) == {"hi": 2, "hello": 5}
word_lengths([]) == {}
```

### Idiom

A dict comprehension.

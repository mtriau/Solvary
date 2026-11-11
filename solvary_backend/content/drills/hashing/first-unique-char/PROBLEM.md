# First non-repeating character

Return the index of the first character in `s` that appears exactly once, or `-1` if every character repeats.

### Signature

`def first_unique(s: str) -> int`

### Examples

```python
first_unique("leetcode") == 0
first_unique("loveleetcode") == 2
first_unique("aabb") == -1
```

### Idiom

Two passes: `Counter(s)` for the counts, then `next((i for i, c in enumerate(s) if counts[c] == 1), -1)` to find the first hit with a default.

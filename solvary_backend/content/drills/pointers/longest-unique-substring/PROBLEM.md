# Longest substring without repeats

Return the length of the longest substring of `s` with no repeated characters. Linear time.

### Signature

`def longest_unique(s: str) -> int`

### Examples

```python
longest_unique("abcabcbb") == 3     # "abc"
longest_unique("bbbbb") == 1
longest_unique("pwwkew") == 3       # "wke"
longest_unique("") == 0
```

### Idiom

Sliding window `[left, right]` with a dict of each character's last index. When `s[right]` was last seen inside the window, jump `left` past it: `left = max(left, last[c] + 1)`. Track `best = max(best, right - left + 1)`.

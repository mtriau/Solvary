# Palindrome ignoring punctuation

Return whether `s` reads the same forwards and backwards once you ignore everything that is not a letter or digit and ignore case.

### Signature

`def is_palindrome(s: str) -> bool`

### Examples

```python
is_palindrome("A man, a plan, a canal: Panama") is True
is_palindrome("race a car") is False
is_palindrome("") is True
```

### Idiom

Normalise first, compare second: `cleaned = [c.casefold() for c in s if c.isalnum()]` then `cleaned == cleaned[::-1]`. The two-pointer version (`left`/`right` converging, skipping non-alphanumerics) is the O(1) extra space follow-up.

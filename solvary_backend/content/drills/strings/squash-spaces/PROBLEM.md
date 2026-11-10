# Squash whitespace

Collapse every run of whitespace (spaces, tabs, newlines) into a single space, and drop leading and trailing whitespace.

### Signature

`def squash_spaces(text: str) -> str`

### Examples

```python
squash_spaces("  hello   world ") == "hello world"
squash_spaces("a\tb\n\nc") == "a b c"
squash_spaces("   ") == ""
```

### Idiom

`" ".join(text.split())`. No regex.

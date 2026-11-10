# Set of initials

Return the set of upper-case first letters of the given names. Ignore names that are empty or only whitespace, and ignore surrounding whitespace on the rest.

### Signature

`def initials(names: list[str]) -> set[str]`

### Examples

```python
initials(["alice", "Bob", "  carol", "anna"]) == {"A", "B", "C"}
initials(["", "   "]) == set()
```

### Idiom

A set comprehension with a filter. The set does the de-duplication for you.

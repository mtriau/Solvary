# Group anagrams by a canonical key

Group words that are anagrams of each other. Return the groups in the order their first member appears; within a group keep input order.

### Signature

`def group_anagrams(words: list[str]) -> list[list[str]]`

### Examples

```python
group_anagrams(["eat", "tea", "tan", "ate", "nat", "bat"]) == [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]
group_anagrams([]) == []
```

### Idiom

A canonical key per word (`"".join(sorted(word))`) into a `defaultdict(list)`. The dict preserves first-seen order, so `list(groups.values())` is the answer.

# Next greater element

For each position, return the first value to its right that is strictly greater, or `-1` if none exists.

### Signature

`def next_greater(nums: list[int]) -> list[int]`

### Examples

```python
next_greater([2, 1, 2, 4, 3]) == [4, 2, 4, -1, -1]
next_greater([5, 4, 3]) == [-1, -1, -1]
```

### Idiom

A monotonic stack of **indices** whose values are waiting for a greater element. When a new value arrives, pop every index whose value is smaller and record the answer for it. One pass, O(n).

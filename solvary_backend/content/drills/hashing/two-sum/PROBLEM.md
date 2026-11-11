# Two sum with one pass

Return the indices `(i, j)` with `i < j` of two numbers in `nums` that add to `target`, or `None` if there is no such pair. If several pairs exist, return the one whose `j` is smallest.

### Signature

`def two_sum(nums: list[int], target: int) -> tuple[int, int] | None`

### Examples

```python
two_sum([2, 7, 11, 15], 9) == (0, 1)
two_sum([3, 3], 6) == (0, 1)
two_sum([1, 2], 7) is None
```

### Idiom

One pass with a dict from value to index. For each number ask "have I already seen `target - x`?" before you store `x`. That order handles `[3, 3]` without special cases.

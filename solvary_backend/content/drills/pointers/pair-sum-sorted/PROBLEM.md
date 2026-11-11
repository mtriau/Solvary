# Pair with a given sum in a sorted list

`nums` is sorted ascending. Return a pair of **values** `(a, b)` with `a <= b` and `a + b == target`, or `None`. If several pairs exist, return the one with the smallest `a`. Linear time.

### Signature

`def pair_sum(nums: list[int], target: int) -> tuple[int, int] | None`

### Examples

```python
pair_sum([1, 2, 4, 7, 11], 9) == (2, 7)
pair_sum([1, 2, 4, 7, 11], 100) is None
pair_sum([3, 3], 6) == (3, 3)
```

### Idiom

Converging pointers: `lo, hi = 0, len(nums) - 1`; `while lo < hi:` compute the sum, then move `lo` right if it is too small, `hi` left if too big, return if equal. Sortedness is what makes each move safe.

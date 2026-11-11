# Binary search: lower bound

Return the index of the first element of sorted `a` that is `>= x`, or `len(a)` if all are smaller. Do it in O(log n) sequence accesses.

### Signature

`def lower_bound(a: Sequence[int], x: int) -> int`

### Examples

```python
lower_bound([1, 3, 3, 5], 3) == 1
lower_bound([1, 3, 3, 5], 4) == 3
lower_bound([1, 3, 3, 5], 9) == 4
lower_bound([], 1) == 0
```

### Idiom

Half-open interval `lo, hi = 0, len(a)` with `while lo < hi:`. `mid = (lo + hi) // 2`; if `a[mid] < x` the answer is right of `mid` (`lo = mid + 1`), otherwise `mid` could be it (`hi = mid`). `return lo`. The invariant: every index before `lo` is `< x`, every index at or after `hi` is `>= x`.

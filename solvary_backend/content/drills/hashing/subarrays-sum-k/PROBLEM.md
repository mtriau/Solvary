# Count subarrays that sum to k

Count the contiguous subarrays of `nums` whose elements sum to exactly `k`. Numbers may be negative or zero.

### Signature

`def count_subarrays(nums: list[int], k: int) -> int`

### Examples

```python
count_subarrays([1, 1, 1], 2) == 2
count_subarrays([1, 2, 3], 3) == 2       # [1, 2] and [3]
count_subarrays([0, 0], 0) == 3          # [0], [0], [0, 0]
```

### Idiom

Running prefix sum plus a `Counter` of prefix sums seen so far, seeded with `{0: 1}`. At each step the number of subarrays ending here with sum `k` is `seen[prefix - k]`.

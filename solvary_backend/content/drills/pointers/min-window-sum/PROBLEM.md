# Shortest subarray with sum at least k

`nums` contains positive integers. Return the length of the shortest contiguous subarray whose sum is at least `k`, or `0` if none exists. Linear time.

### Signature

`def min_window_sum(nums: list[int], k: int) -> int`

### Examples

```python
min_window_sum([2, 3, 1, 2, 4, 3], 7) == 2     # [4, 3]
min_window_sum([1, 1, 1], 5) == 0
min_window_sum([10], 7) == 1
```

### Idiom

Grow-and-shrink window: `for right, x in enumerate(nums)`: add `x` to the running sum, then `while total >= k:` record `right - left + 1`, subtract `nums[left]`, advance `left`. Use `best = min(best, ...)` starting from `math.inf` and return `0` if it never changed.

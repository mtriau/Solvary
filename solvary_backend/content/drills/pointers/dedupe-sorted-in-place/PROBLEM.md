# Remove duplicates from a sorted list in place

`nums` is sorted. Move the distinct values to the front of the list, in order, and return how many there are. Only the first `k` positions matter afterwards; do not allocate a second list.

### Signature

`def dedupe_sorted(nums: list[int]) -> int`

### Examples

```python
nums = [1, 1, 2, 3, 3]
k = dedupe_sorted(nums)
k == 3 and nums[:k] == [1, 2, 3]
```

### Idiom

A **write index**. Walk the list with `for x in nums[1:]`-style reads; whenever `x` differs from the last written value, write it at `nums[write]` and advance `write`. The read pointer is the loop, the write pointer is yours.

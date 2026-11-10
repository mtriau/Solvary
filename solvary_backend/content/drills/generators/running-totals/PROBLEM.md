# Running totals

Return the running (cumulative) totals of a list of numbers.

### Signature

`def running_totals(nums: list[int]) -> list[int]`

### Examples

```python
running_totals([1, 2, 3, 4]) == [1, 3, 6, 10]
running_totals([5, -5, 5]) == [5, 0, 5]
running_totals([]) == []
```

### Idiom

`itertools.accumulate`.

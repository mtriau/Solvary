# Squares of the evens

Return the square of every even number in `nums`, in the original order.

### Signature

`def squares_of_evens(nums: list[int]) -> list[int]`

### Examples

```python
squares_of_evens([1, 2, 3, 4]) == [4, 16]
squares_of_evens([-2, 0, 7]) == [4, 0]
squares_of_evens([]) == []
```

### Idiom

A list comprehension with a filter. No empty list, no `append`.

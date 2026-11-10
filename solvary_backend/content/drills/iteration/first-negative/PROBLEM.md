# First negative number

Return the first negative number in `nums`, or `None` if there is none. Stop reading the input as soon as you find it: `nums` may be a lazy iterator, and consuming past the first negative is wrong.

### Signature

`def first_negative(nums) -> int | None`

### Examples

```python
first_negative([3, -1, -5]) == -1
first_negative([1, 2]) is None
```

### Idiom

`next` on a generator expression, with a default.

# Digits in another base

Return the digits of non-negative `n` in base `base` (2 to 36), most significant first, as integers. Zero is `[0]`.

### Signature

`def to_base(n: int, base: int) -> list[int]`

### Examples

```python
to_base(10, 2) == [1, 0, 1, 0]
to_base(255, 16) == [15, 15]
to_base(0, 7) == [0]
```

### Idiom

`while n: n, d = divmod(n, base); digits.append(d)` peels digits off least-significant first; `digits[::-1] or [0]` flips them and handles zero.

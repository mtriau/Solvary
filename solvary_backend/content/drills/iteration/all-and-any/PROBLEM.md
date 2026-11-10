# all and any

Two one-liners about a list of exam scores.

### Signature

```python
def all_passed(scores: list[int], threshold: int) -> bool
def any_failed(scores: list[int], threshold: int) -> bool
```

`all_passed` is true when every score is at least `threshold`. `any_failed` is true when at least one score is below it.

### Examples

```python
all_passed([70, 85], 60) is True
all_passed([70, 55], 60) is False
any_failed([70, 55], 60) is True
all_passed([], 60) is True      # vacuous truth
any_failed([], 60) is False
```

### Idiom

`all(...)` and `any(...)` over generator expressions. They must return real booleans.

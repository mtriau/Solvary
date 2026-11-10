# A Point dataclass

Define an immutable `Point` with integer fields `x` and `y` and a method `distance_to(other)` returning the Euclidean distance as a float. Points with equal coordinates must compare equal, be usable in sets, and print as `Point(x=1, y=2)`. Assigning to a field must raise `dataclasses.FrozenInstanceError`.

### Signature

```python
class Point:
    x: int
    y: int
    def distance_to(self, other: "Point") -> float: ...
```

### Examples

```python
Point(1, 2) == Point(1, 2)
repr(Point(1, 2)) == "Point(x=1, y=2)"
Point(0, 0).distance_to(Point(3, 4)) == 5.0
len({Point(1, 1), Point(1, 1)}) == 1
```

### Idiom

`@dataclass(frozen=True)` and `math.hypot`. No hand-written `__init__`, `__eq__`, `__hash__` or `__repr__`.

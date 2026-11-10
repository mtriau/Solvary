### Why this is idiomatic

- `@dataclass` generates `__init__`, `__repr__` and `__eq__` from the field annotations. `frozen=True` adds immutability and, together with `eq`, a `__hash__`, which is what makes the points usable in sets and as dict keys. That is five dunder methods you did not write and cannot get subtly wrong.
- The generated `__repr__` is exactly `Point(x=1, y=2)`; the suite pins it to make sure you did not hand-roll one.
- `math.hypot(dx, dy)` is the distance formula by name, and it is more numerically careful than `sqrt(dx*dx + dy*dy)`.
- A `NamedTuple` would also satisfy everything here. Dataclasses are the default choice when you may add methods or mutable variants later.

### The habit

A class that mainly holds data is a dataclass. Write `__init__` by hand only when construction does real work.

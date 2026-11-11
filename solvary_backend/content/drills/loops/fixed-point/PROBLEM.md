# Iterate to a fixed point

Apply `f` repeatedly starting from `x` until two consecutive values differ by at most `tol`, and return the last value. Give up with `ValueError` after `max_steps` applications.

### Signature

`def fixed_point(f: Callable[[float], float], x: float, tol: float = 1e-9, max_steps: int = 1000) -> float`

### Examples

```python
fixed_point(math.cos, 1.0)                      # ~0.7390851332
fixed_point(lambda v: (v + 2 / v) / 2, 1.0)     # ~1.4142135624 (Newton for sqrt 2)
fixed_point(lambda v: v + 1, 0.0, max_steps=5)  # raises ValueError
```

### Idiom

A `for _ in range(max_steps)` loop with `return` inside and `raise` after it. The step cap is the loop bound, not a counter you maintain by hand. Use the walrus to compute the next value once: `if abs((nxt := f(x)) - x) <= tol: return nxt`.

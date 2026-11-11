# Moving averages with a bounded deque

Return the average of the last `k` values after each value in `values` is seen. Early on, when fewer than `k` values have arrived, average what there is.

### Signature

`def moving_averages(values: Iterable[float], k: int) -> list[float]`

### Examples

```python
moving_averages([1, 2, 3, 4], 2) == [1.0, 1.5, 2.5, 3.5]
moving_averages([10, 20, 30], 5) == [10.0, 15.0, 20.0]
moving_averages([], 3) == []
```

### Idiom

`deque(maxlen=k)` drops the oldest value for you when a new one is appended. Each step is `window.append(x)` then `sum(window) / len(window)`.

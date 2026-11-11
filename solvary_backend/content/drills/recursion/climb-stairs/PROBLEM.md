# Climbing stairs with memoisation

You can climb 1 or 2 steps at a time. Return the number of distinct ways to climb `n` steps. `n` can be several hundred, so naive recursion will not finish.

### Signature

`def climb(n: int) -> int`

### Examples

```python
climb(0) == 1     # one way: do nothing
climb(1) == 1
climb(2) == 2
climb(5) == 8
```

### Idiom

Write the recurrence as the obvious recursive function and put `@functools.cache` on it. Base cases first (`if n < 2: return 1`), then `return climb(n - 1) + climb(n - 2)`. The bottom-up loop with two variables is the follow-up.

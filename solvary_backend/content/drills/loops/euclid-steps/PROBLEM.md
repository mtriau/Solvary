# Count the steps of Euclid's algorithm

Return how many modulo steps Euclid's algorithm takes to find `gcd(a, b)`: the number of times `a, b = b, a % b` runs before `b` becomes zero.

### Signature

`def euclid_steps(a: int, b: int) -> int`

### Examples

```python
euclid_steps(12, 8) == 2      # (12, 8) -> (8, 4) -> (4, 0)
euclid_steps(8, 12) == 3      # (8, 12) -> (12, 8) -> (8, 4) -> (4, 0)
euclid_steps(5, 0) == 0
```

### Idiom

`while b: a, b = b, a % b; steps += 1`. The tuple assignment swaps and reduces at once with no temporary.

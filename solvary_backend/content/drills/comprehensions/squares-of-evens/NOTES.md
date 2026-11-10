### Why this is idiomatic

- A comprehension says *what* the list is (`n * n` for each even `n`) instead of *how* to build it. The loop-and-append version has three statements and a mutable accumulator for the same idea.
- The filter lives in the comprehension's `if` clause. Resist `map` + `filter` + `lambda` here; the comprehension reads left to right.
- `n % 2 == 0` is the standard evenness test; it is correct for negatives too (`-2 % 2 == 0`).

### The clunky version

```python
result = []
for n in nums:
    if n % 2 == 0:
        result.append(n ** 2)
return result
```

### The habit

When you catch yourself writing `x = []` followed by a loop that only appends, write a comprehension instead.

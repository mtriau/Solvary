# All subsets by backtracking

Return every subset of `items` (the power set) as a list of lists. Order of subsets does not matter; order within a subset follows `items`.

### Signature

`def subsets(items: list[int]) -> list[list[int]]`

### Examples

```python
sorted(subsets([1, 2])) == [[], [1], [1, 2], [2]]
subsets([]) == [[]]
```

### Idiom

Backtracking: a recursive `go(start, chosen)` that records `chosen` and then, for each `i` from `start`, appends `items[i]`, recurses with `i + 1`, and pops. The append/recurse/pop triple is the shape of every backtracking problem.

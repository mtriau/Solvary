### Why this is idiomatic

- `accumulate` is the standard library's prefix-sum. One import, one call, and it generalises: `accumulate(nums, max)` gives running maxima, `accumulate(nums, initial=0)` prepends a zero.
- The loop with `total += n; out.append(total)` is honest Python too, but it carries state by hand for something a name already exists for.
- Wrapping in `list(...)` is needed because `accumulate` returns an iterator; the spec asks for a list.

### The habit

Scan `itertools` once. `accumulate`, `chain`, `groupby`, `pairwise`, `islice` and `product` replace a great deal of hand-written loop machinery.

### Why this is idiomatic

- Half-open `[lo, hi)` with `while lo < hi` is the binary search that does not have off-by-one bugs. There is no `hi = mid - 1`, no `<=`, no `return -1` branch: when the loop ends, `lo == hi` and that is the answer.
- Say the invariant and you can derive both updates: "everything left of `lo` is too small, everything from `hi` on is big enough." If `a[mid] < x`, `mid` is too small, so `lo = mid + 1`. Otherwise `mid` is big enough and might be the first, so `hi = mid` (keep it in range).
- Termination: the range shrinks every iteration because `mid < hi`, so `mid + 1 <= hi` and `mid >= lo`.
- `bisect.bisect_left(a, x)` is this function. Use it in real code, write it by hand in interviews when asked, and test the `Counting` sequence either way: a linear scan reads a million elements.

### The habit

Binary search is four lines once you fix the convention: half-open, `while lo < hi`, move `lo` past or `hi` onto. Pick it once and never vary it.

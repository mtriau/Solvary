### Why this is idiomatic

- The two `if`s are the rules of the problem stated directly: an opener is allowed while openers remain, a closer is allowed while there are unmatched openers. Because the rules are checked *before* recursing, every leaf is valid and no filtering step is needed.
- Strings are immutable, so `partial + "("` creates the next state and there is nothing to un-choose; with a list you would `append`/`pop` as in the subsets drill. Both are backtracking; the immutable version just hides the undo.
- The base case is checked first, by length, which is the simplest possible test. `opened == closed == n` would also work.
- Counting the results (Catalan numbers: 1, 1, 2, 5, 14, 42, 132) is how you verify the pruning without reading every string.

### The habit

Generate-all-valid-X problems: write the base case, then one `if` per allowed move with the constraint as its condition. If you find yourself generating everything and filtering, the constraints belong in the recursion.

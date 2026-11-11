### Why this is idiomatic

- Why each move is safe: if `nums[lo] + nums[hi] < target`, then `nums[lo]` paired with *anything* at or left of `hi` is also too small, so `lo` can never be part of the answer with the current `hi` or anything smaller. Advance it. The mirror argument moves `hi`. Say this in the interview; it is the whole proof.
- `while lo < hi` stops before the pointers meet, so an element never pairs with itself (the `[4], 8` test).
- Three outcomes per step, three lines: return, move `lo`, move `hi`. No nested `if`.
- The dict approach from two-sum also works in O(n) but uses O(n) space and ignores the sortedness. When the input is sorted, converging pointers is the expected answer.

### The habit

Sorted input plus "find a pair" is two pointers from the ends. Write the `while lo < hi` and the three-way comparison before anything else.

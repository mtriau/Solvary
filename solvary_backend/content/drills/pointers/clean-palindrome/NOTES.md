### Why this is idiomatic

- Separate the cleaning from the comparison. `[c.casefold() for c in s if c.isalnum()]` says exactly which characters count, and `cleaned == cleaned[::-1]` is the palindrome test in five tokens.
- `casefold()` is the correct case-insensitive normalisation (it handles `ß` and friends); `lower()` is fine in an interview, but know why `casefold` exists.
- The two-pointer version in the reference is what to write when the interviewer says "without extra space". Its shape, `while left < right` with the three skip/mismatch/advance branches, is the standard converging-pointers loop. Note the exit condition: `left < right`, not `<=`, because a middle character matches itself.

### The habit

Normalise, then compare. Reach for `[::-1]` for "reversed" and for converging pointers only when space is the question.

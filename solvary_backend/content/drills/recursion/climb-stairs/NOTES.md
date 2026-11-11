### Why this is idiomatic

- The recursive definition *is* the specification: the ways to reach step n are the ways to reach n-1 (then step 1) plus the ways to reach n-2 (then step 2). Writing it that way and caching is the fastest route to a correct answer in an interview.
- `@functools.cache` (3.9+) turns the exponential tree into n calls. `@lru_cache(maxsize=None)` is the same thing on older Pythons. Say "memoise" when you add it, and say the complexity changed from O(2^n) to O(n).
- Base cases first, in a guard clause, before the recursive case. `n < 2` covers both 0 and 1 in one line.
- Recursion depth is n, so `climb(500)` is safe but `climb(5000)` would not be. The two-variable loop in the reference is the constant-space, no-recursion-limit version to offer as the follow-up.

### The habit

For "count the ways" problems, write the recurrence, cache it, verify small cases, then convert to a loop if depth or space is raised. Do not start with the loop; start with the definition.

### Why this is idiomatic

- The nested loop ("for each i, scan right until bigger") is quadratic, and the decreasing test makes it scan the whole tail every time.
- The stack holds indices whose answers are unknown. It stays in decreasing order of value, which is why the inner `while` pops only what the new element resolves and never looks at anything else. Every index is pushed once and popped at most once: O(n).
- The `while` condition carries the invariant: "the top is smaller than me, so I am its answer". When it stops, either the stack is empty or the top is at least as big, so I wait too.
- Pre-filling `result = [-1] * len(nums)` makes "no greater element" the default and removes a clean-up loop.

### The habit

"Next greater / smaller / warmer to the left or right" is a monotonic stack. Write the `while` pop condition first; everything else follows from it.

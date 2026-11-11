### Why this is idiomatic

- Two loops, but still linear: `right` advances n times in the `for`, and `left` advances at most n times in total across all the inner `while` runs. Each element enters and leaves the window once. Say that when asked for the complexity.
- The `while` condition is the invariant you want to break: "while the window is big enough, record it and try smaller". Shrinking stops exactly when the sum drops below `k`, which is the only moment the window can be minimal for this `right`.
- `math.inf` as the initial `best` means "no answer yet" and lets you use `min` without a special case; translate to the contract's `0` once, at the end.
- Positive numbers are what make this work: adding never shrinks the sum and removing never grows it. With negatives you need prefix sums and a monotonic deque instead, which is the follow-up.

### The habit

Variable-size window: outer `for` grows from the right, inner `while` shrinks from the left while the condition holds. Decide which side records the answer (here, inside the shrink) and keep `best` as `inf` or `-inf` until the end.

### Why this is idiomatic

- `divmod` gives quotient and remainder in one call, and `n, d = divmod(n, base)` advances the loop and captures the digit in one line. `n // base` and `n % base` on separate lines compute the division twice and read slower.
- The exit condition is `while n:`. The loop runs while there is something left to divide; when `n` reaches 0 there are no more digits. Zero never enters the loop, which is why `or [0]` is needed and why it is the whole special case.
- `str(n)` tricks only work for base 10. The loop works for any base, which is the point.

### The habit

"Peel something off the end repeatedly" is `while n:` with `divmod`. Decide what the loop variable means ("the part not yet converted") and the exit condition writes itself.

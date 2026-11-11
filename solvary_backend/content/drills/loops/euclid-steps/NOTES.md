### Why this is idiomatic

- `a, b = b, a % b` is the whole algorithm. The right-hand side is evaluated fully before either name is rebound, so no `tmp` variable is needed. This is the same tuple swap as `a, b = b, a`.
- `while b:` is the exit condition stated as "while there is a remainder". Testing `b != 0` is identical but noisier.
- `math.gcd` would give the answer, but not the step count. Interviewers ask for the loop when they want to see you reason about what each iteration preserves: here, `gcd(a, b)` is unchanged by every step.

### The habit

Two values that update together get one tuple assignment. Say the loop invariant ("gcd is preserved, b strictly decreases") and the termination argument comes free.

### Why this is idiomatic

- `for _ in range(max_steps)` is the step cap. A `while True` with `steps += 1` and `if steps > max_steps` is three extra lines and one off-by-one waiting to happen (the test counts calls exactly).
- `return` inside the loop and `raise` after it make the two exits visible: converged, or ran out. The code after the loop is only reached when the loop finished without returning.
- The walrus `(nxt := f(x))` evaluates `f` once per step and keeps the comparison on the same line as the assignment. Calling `f(x)` twice would double the work and break the call-count tests.
- Return `nxt`, not `x`: it is the better approximation, and it is what `abs(f(result) - result) <= tol` checks.

### The habit

Bounded iteration is a `for` over `range`. `while` is for loops whose bound you do not know. When a loop has two ways to end, make one a `return`/`break` inside and handle the other after the loop.

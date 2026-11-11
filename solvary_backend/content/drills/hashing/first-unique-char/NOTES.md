### Why this is idiomatic

- Count first, then scan: two linear passes. The quadratic version (`s.count(c)` inside the loop) is the trap, and the last test is sized so it does not finish.
- `next(generator, default)` is the "find first or fallback" idiom. It stops at the first match and does not build a list.
- `enumerate` because you need the index. `Counter` because you are counting.

### The habit

"First element satisfying P, else sentinel" is `next((... if P), sentinel)`. Pair it with a precomputed dict whenever P needs information about the whole input.

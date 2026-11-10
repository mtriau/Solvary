### Why this is idiomatic

- `max(words, key=len)` is a single linear pass and says exactly "the biggest by length". Sorting to take the last element is O(n log n) for a question that needs O(n), and reads as a workaround.
- `max` returns the *first* maximal element, so the tie rule comes for free.
- `default=None` handles the empty case; without it `max` raises `ValueError`. No `if not words` guard needed.
- Because `max` consumes any iterable, the function works on generators too, which the suite checks.

### The habit

"The largest/smallest by some property" is `max`/`min` with a `key`, not a sort.

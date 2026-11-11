### Why this is idiomatic

- Matching nested things is *the* stack problem. A plain list with `append`/`pop` is the Python stack; there is no separate class to reach for.
- The closer-to-opener dict replaces three `if` branches, and `ch in PAIRS.values()` reads as "is an opener".
- Two exit conditions, both stated plainly: a closer with an empty stack or a mismatch fails immediately; at the end, anything still open fails. `return not stack` says the second one in three words.
- `stack.pop() != PAIRS[ch]` after `not stack or` relies on short-circuit evaluation so you never pop an empty list.

### The habit

When later input must undo earlier input in reverse order, say "stack" before you type anything. Then write the two exit conditions first.

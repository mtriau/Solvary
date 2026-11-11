### Why this is idiomatic

- Kahn's algorithm is BFS over "what is ready". The three pieces are always the same: in-degree counts, a reverse adjacency (who is waiting on me), and a queue of zero-in-degree nodes. Build them in that order, out loud.
- Cycle detection falls out for free: nodes on a cycle never reach in-degree 0, so they never enter the order. Comparing `len(order)` with `len(deps)` is the check. No colours, no recursion.
- The dict comprehension `{task: len(needs) ...}` sets the in-degrees in one line because the input is already "task to dependencies".
- A `deque` is correct here, but since order within the ready set does not matter, a plain list used as a stack also works. Use the deque if you want a stable, breadth-first flavoured order like the chain test expects.

### The habit

"Order things so prerequisites come first" or "detect a dependency cycle": Kahn's. In-degree, reverse map, ready queue, pop-append-decrement, length check.

### Why this is idiomatic

- "For each unvisited node, flood its component, count one" is the component-counting skeleton. The outer loop over `graph` finds new components; the inner traversal marks them.
- Iterative DFS is a `while stack:` loop over a list. A 5,000-node chain overflows Python's recursion limit (1,000), which is why the last test exists. BFS with a deque works identically here; DFS with a list is one fewer import.
- `seen` lives outside both loops. Re-creating it per start, or forgetting to mark the start, both show up as wrong counts on the triangles.
- Mark on push, like BFS. Marking on pop allows the same node to be pushed by several neighbours and makes dense graphs quadratic.

### The habit

Components, islands, flood fill: outer `for` over all nodes guarded by `seen`, inner iterative traversal. Keep a single `seen` and mark before you push.

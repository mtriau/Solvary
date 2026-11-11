### Why this is idiomatic

- `defaultdict(set)` makes "add `v` to `u`'s neighbours, creating the entry if needed" a single statement. The `if u not in graph: graph[u] = set()` dance is what it replaces.
- Sets as neighbour collections give O(1) `in` checks and collapse duplicate edges for free. Use a list only when edge multiplicity or order matters.
- Converting back with `dict(graph)` stops a later typo (`graph["zzz"]`) from silently inventing a node, which is the classic defaultdict leak. The last test checks it.
- The two `add` lines are the "undirected" part. Say "directed would be just the first line" when you write them.

### The habit

Every graph problem starts with ten seconds of "build the adjacency": `defaultdict(set)` or `defaultdict(list)`, one loop over edges. Have it in your fingers so you can talk about the actual algorithm while you type it.

### Why this is idiomatic

- The Kahn version is the one to reach for under time pressure: it is the previous drill with the order list replaced by a count, no recursion, and the proof is one sentence ("a node on a cycle can never become ready").
- The DFS version is what interviewers mean by "colour the nodes". The point to get right is **grey versus black**: a grey node is an ancestor on the current path, so an edge to it closes a cycle; a black node is finished, and an edge to it is a diamond, not a cycle. Using a single `visited` set conflates the two and reports the diamond as a cycle.
- Making DFS iterative means keeping an iterator of children per frame (`iter(graph[node])`) so you can resume where you left off, and `for ... else` to notice when a node's children are exhausted. It is fiddly, which is exactly why Kahn's wins at the whiteboard.
- Both must be linear and recursion-free; the 4,000-node chains fail a recursive solution.

### The habit

Directed cycle: Kahn's by default, three-colour DFS when the question is specifically about DFS. Undirected cycle is a different problem (union-find or "visited neighbour that is not my parent"). Say which one you are solving.

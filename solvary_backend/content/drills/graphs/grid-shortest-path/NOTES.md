### Why this is idiomatic

- BFS gives shortest paths in unweighted graphs because it explores in order of distance. The queue is a `deque`; `list.pop(0)` is O(n) and will show on the large grid.
- Mark `seen` when you enqueue. Marking when you pop lets the same cell be enqueued many times from different neighbours, which on an open grid multiplies the work and can blow up memory. This is the single most common BFS bug.
- Carrying the distance in the queue entry (`(cell, dist)`) avoids a separate distance dict or level-by-level loop. Both alternatives are fine; pick one and be consistent.
- A `DIRS` constant and `nr, nc = r + dr, c + dc` is the standard grid-neighbour shape. The one long `if` keeps bounds, walls and visited together so none is forgotten.

### The habit

BFS skeleton: deque seeded with the start, `seen` containing the start, `while queue:` pop left, check goal, push unseen neighbours **after** marking them. Type it without thinking; think about the neighbour rule instead.

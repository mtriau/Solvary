# Comment Tree Filter: Part 3

The same module grows once more: produce the thread the viewer actually sees,
in display order. The filter from Parts 1 and 2 stays as it is; this part
adds ordering and depth, plus one rule about what happens when a kept comment
sits under an excluded one. The earlier tests still run.

### What to implement

- `render_thread(comments, mode, threshold: int | None = None) -> list[tuple[int, int]]`
  returns the visible comments as `(depth, id)` pairs in display order.

### Rules

- "Visible" means exactly `visible_comments(comments, mode, threshold)`.
- Top-level comments come first, sorted by `points` descending, then `id`
  ascending. Each is immediately followed by its visible descendants,
  depth-first, with siblings sorted the same way.
- A top-level comment has depth 0; a child is one deeper than its displayed
  parent.
- Excluded comments, and the subtrees the filter excludes with them, never
  appear.
- **Re-parenting.** Part 2 can keep a qualifying hidden comment whose parent
  is excluded. It is attached to its **nearest visible ancestor** and its
  depth is that ancestor's depth plus one. If it has no visible ancestor it
  becomes a top-level comment at depth 0. It then sorts among its new
  siblings like any other. This is how a collapsed ancestor is skipped over.
- Depth is the depth in the displayed thread, not in the original tree.
- Stay iterative; trees can be 200k deep.

### Worked example

The forest from Part 2, in cat mode with `threshold=10`:

```python
render_thread(comments, "cat", threshold=10)
# -> [(0, 16), (0, 10), (1, 11), (2, 12)]
```

Comment 16 was kept but its parent 15 is excluded and nothing visible is
above it, so it is top-level; its 30 points put it ahead of comment 10
(1 point). Under 10, comment 11 shows at depth 1 with its cat child 12 at
depth 2; 13 and 14 are excluded.

```python
render_thread(comments, "cat")   # -> [(0, 10)]
```

### Clarifications

- **Ties on points?** Lower id first, at every level.
- **Where does a re-parented comment go?** Among its new siblings, ordered by
  its own points and id.
- **Depth of a re-parented comment?** Nearest visible ancestor's depth plus 1.
- **Everything excluded?** Return `[]`.
- **Errors?** Same `ValueError` cases as before.
- **Input order?** Irrelevant to the display order, except that it is not used
  to break ties; ids are.

Run the provided tests with **Submit**; the earlier tests run too.

---
Interviewer notes

The sort key is the easy part; the re-parenting sentence is the real test.
Candidates who keep the original parent produce depths that skip levels or
drop the kept comment entirely. A neat approach is to compute, in the same
top-down pass as Part 2, the nearest visible ancestor of each node and build
the display children lists from that. Listen for whether they keep the
traversal iterative when they reach the output pass.

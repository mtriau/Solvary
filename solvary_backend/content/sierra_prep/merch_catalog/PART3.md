# Merchandise Catalog: Part 3

Real catalogs have cycles ("tent" relates to "stakes", which relates back
to "tent") and are large. Make the traversal safe and bounded.

### What to implement

1. `related_tree(catalog, item_id, max_depth=None)`, extended:
   - **Cycle cut by path.** An item that is already on the path from the
     root to the current node is **omitted** from that node's children. The
     same item may still appear in different branches, as in Part 2.
   - **Depth limit.** The root is at depth 0. With `max_depth=d`, nodes at
     depth `d` get `"related": []` and nothing deeper is expanded.
     `max_depth=0` gives just the root. `None` means unlimited.
2. `reachable(catalog, item_id, max_depth=None) -> list[str]`: every item
   reachable from `item_id` through `related` links, **excluding `item_id`
   itself**, each exactly once, in **breadth-first order**: by increasing
   depth, and within one depth in discovery order (parents in BFS order,
   each parent's `related` list in order). `max_depth` bounds the number of
   links followed; `max_depth=0` gives `[]`. `[]` for an unknown item.
3. Both must handle a catalog of 50,000 items quickly (roughly linear
   time).

### Worked example

```python
cat = {"a": rel("b", "c"), "b": rel("a", "d"), "c": rel("d"), "d": rel("a")}
reachable(cat, "a")               # -> ["b", "c", "d"]
reachable(cat, "a", max_depth=1)  # -> ["b", "c"]
related_tree(cat, "a", max_depth=2)
# -> {"id": "a", "related": [
#       {"id": "b", "related": [{"id": "d", "related": []}]},     # "a" omitted (on path)
#       {"id": "c", "related": [{"id": "d", "related": []}]}]}
```

(`rel(*ids)` builds a record with those related ids.) In the tree, `b`'s
children are `a` and `d`; `a` is on the path `a -> b`, so it is cut. `d`
appears under both `b` and `c`, because it is on neither path. Without
`max_depth` the result is the same here: `d`'s only child is `a`, which is
always on the path.

### Clarifications

- **Path-based cut versus a global visited set?** They differ. A global
  visited set would make `d` disappear from the `c` branch after it was
  seen under `b`. The tests require the path rule: only ancestors of the
  current node are excluded.
- **An item related to itself?** Omitted from its own children (it is on
  the path). `reachable` never lists the start item, even when a cycle leads
  back to it.
- **Breadth-first order, precisely?** For `r: [b, a]`, `a: [z]`,
  `b: [y, a]`: `reachable(cat, "r")` starts `["b", "a", "y", "z", ...]`.
  `b` before `a` (r's list order), then `y` (b's first child), and `a` is
  not repeated.
- **What does `max_depth` count for `reachable`?** Links from the start.
  `max_depth=1` is the direct related items only.
- **Why must the path be per branch?** When you return from a branch, its
  items must become allowed again for sibling branches. With an explicit
  stack, carry the path (as a set or tuple) along with each frame.
- **Is `related_items` from Part 2 still the building block?** Yes. It
  already skips unknown ids.

Run the provided tests with **Submit**.

---
Interviewer notes

The bank entry calls this "a cycle-safe tree of related items". A
`visited` set that is never un-marked turns the tree into a DAG walk
(items vanish from later branches); the path-based rule is the
distinguishing detail. `reachable` is plain BFS with a global visited
set.

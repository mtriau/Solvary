# Comment Tree Filter: Part 2

The same module grows. A hidden thread the community loves should not vanish:
Reddit's follow-up gives each comment points and lets a hidden subtree
survive if its total is high enough. The trap is stopping at the first hidden
root and missing a qualifying subtree nested further down. The Part 1 tests
still run, so keep the threshold optional.

### What to implement

- `comments_to_exclude(comments, mode, threshold: int | None = None) -> list[int]`
  gains an optional threshold. `visible_comments` takes the same optional
  argument and stays the complement.
- `subtree_points(comments: list[dict]) -> dict[int, int]` maps every id to
  its subtree total.

### Rules

- A comment's **subtree total** is its own `points` plus the points of all its
  descendants, hidden or not. Points may be negative.
- A hidden-category comment **qualifies** when `threshold` is not `None` and
  its subtree total is **strictly greater** than the threshold.
- Decisions are made top-down. A comment is excluded if and only if the
  **nearest hidden-category comment on its path to the root** (itself
  included) exists and does not qualify. A comment with no hidden-category
  comment on its path is never excluded.
- So a qualifying subtree nested inside a non-qualifying hidden one is shown,
  and a non-qualifying hidden comment nested inside a qualifying one is
  excluded along with its own subtree.
- With `threshold=None` the behaviour is exactly Part 1.
- Compute the totals in one pass over the forest (children folded into
  parents), not by re-walking each subtree. Stay iterative.

### Worked example

```
10 cat  pts 1
   11 dog  pts 5
      12 cat  pts 50
      13 dog  pts -3
   14 dog  pts 2
15 dog  pts -30
   16 dog  pts 30
   17 cat  pts 1
```

```python
subtree_points(comments)
# -> {10: 55, 11: 52, 12: 50, 13: -3, 14: 2, 15: 1, 16: 30, 17: 1}

comments_to_exclude(comments, "cat", threshold=10)   # -> [13, 14, 15, 17]
comments_to_exclude(comments, "cat")                 # -> [11, 12, 13, 14, 15, 16, 17]
```

With threshold 10, comment 11 (total 52) qualifies, so it and its cat child 12
stay, but 13 is its own hidden comment with total -3 and goes. Comment 14
(total 2) goes. Comment 15 (total 1) does not qualify, so its cat child 17
goes with it, yet 16 (total 30) qualifies and is kept even though its parent
is excluded.

### Clarifications

- **Equal to the threshold?** Does not qualify. It must be strictly greater.
- **Do hidden descendants count towards the total?** Yes, and so do visible
  ones, and negative points subtract.
- **Which comment decides?** The nearest hidden-category comment at or above
  it. A visible comment under a qualifying hidden one is kept; under a
  non-qualifying one it is excluded.
- **Does a non-hidden comment ever need to qualify?** No. Only hidden-category
  comments are tested against the threshold.
- **`threshold=None`?** Same as Part 1.
- **Children before parents?** Still possible. Still 200k deep.

Run the provided tests with **Submit**; the Part 1 tests run too.

---
Interviewer notes

Two-pass shape: one post-order pass for the subtree sums, then a top-down pass
that carries the nearest hidden decision. Candidates who prune at the first
hidden root pass the simple threshold tests and fail the nested one, which is
the follow-up Reddit actually asks about. Ask about the equals case before
they code; the answer is strict. Recomputing each subtree sum by walking it is
quadratic on a chain and is caught by the 200k test.

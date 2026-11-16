# Comment Tree Filter: Part 1

Reddit asks this in phone screens and onsites for SWE, MLE and Android roles;
three 2026 reports describe it, and two of the candidates did not finish
part 2 (one still passed). Comments form a forest linked by parent ids, and
each is flagged cat or dog. A viewer who only wants one category must not see
the other, nor anything underneath it. The interviewer wants the forest built
from the parent links in one pass, and the filter rule read exactly as it is
written. Later parts add scores and a display order.

### What to implement

Module `comment_filter`. Each comment is a dict with `id: int`,
`parent: int | None`, `cat: bool`, `dog: bool` and `points: int`.

- `comments_to_exclude(comments: list[dict], mode: str) -> list[int]` returns
  the ids that the viewer must not see, in input order.
- `visible_comments(comments: list[dict], mode: str) -> list[int]` returns the
  complement: the ids that stay, in input order.

### Rules

- `mode` is `"cat"` or `"dog"`; anything else raises `ValueError`.
- A comment is **hidden-category** when it lacks the viewer's flag: in `"cat"`
  mode that means `cat == False`, whatever `dog` says (and the other way
  round in `"dog"` mode).
- Every hidden-category comment is excluded, and so is every descendant of
  one, whatever the descendant's own flags. A cat reply under a dog comment
  is excluded for a cat viewer.
- Ids are unique. `parent` is `None` for a top-level comment. The input order
  is arbitrary: a child may appear before its parent.
- A `parent` that names an id not in the input raises `ValueError`.
- Both functions return ids in the same order as the input list.
- Do not modify the input. `points` is ignored in this part.
- Trees can be 200k deep, so use an explicit stack or queue, not recursion.

### Worked example

```
1  cat
   2  dog
      3  cat
   4  cat
5  dog
   6  cat
      7  cat
         8  cat
```

```python
comments_to_exclude(comments, "cat")   # -> [2, 3, 5, 6, 7, 8]
visible_comments(comments, "cat")      # -> [1, 4]
visible_comments(comments, "dog")      # -> [5]
```

In cat mode comment 3 is a cat, but its parent 2 is hidden, so it goes with
it. Comments 6, 7 and 8 all go with 5. In dog mode comment 1 is not a dog, so
1 to 4 all go, and 6 is hidden under 5, taking 7 and 8 with it.

### Clarifications

- **Does `dog == True` matter in cat mode?** No. Only `cat` is read. A comment
  with both flags is visible in both modes; one with neither is hidden in both.
- **Can children come before parents in the list?** Yes. Build the children
  map first, then traverse.
- **Output order?** Input order, not traversal order.
- **A cat under a dog, is it shown?** No. Hiding removes the whole subtree.
- **A parent id that does not exist?** `ValueError`.
- **An unknown mode?** `ValueError`.
- **How large?** Trees can be 200k deep. A chain of 200,000 comments given
  children first must finish well under 2 seconds without hitting the
  recursion limit.

Run the provided tests with **Submit**.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

The usual slip is reading the rule as "dog and not cat" (`isDog && !isCat`),
which mishandles comments flagged both or neither; the interviewer's answer
was that only `!isCat` matters in cat mode. Watch whether the candidate builds
the forest in one pass rather than searching the list for each comment's
parent, and whether they reach for recursion on a tree that can be 200k deep.
Keep the traversal separate from the rule, since part 2 changes the rule.

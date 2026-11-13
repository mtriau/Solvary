# Recipe Shopping Cart: Part 2

The same `Cart` grows a history. Every change to the cart becomes a
version, and you can go back to an earlier one. The Part 1 tests still run
alongside the new ones.

### What to implement

- `get_version() -> int`: the current version number.
- `checkout(version: int) -> bool`: restore the cart to exactly the state it
  had at that version and **discard every newer version**. Returns `True`,
  or `False` (changing nothing) if that version does not exist.

### Rules

1. A new cart is **version 0**.
2. Every **effective** mutation creates a new version: an `add_recipe` or
   `remove_recipe` that returned `True`. Calls that returned `False` create
   nothing.
3. Reads (`get_version`, `get_total_discount`, `ingredient_counts`) and
   `checkout` itself never create a version.
4. After `checkout(v)` the current version is `v`, and versions above `v`
   no longer exist: `checkout` to them returns `False`.
5. The next effective mutation after a checkout continues numbering from the
   restored version. After versions 1 and 2, `checkout(1)` followed by an
   `add_recipe` makes a brand-new version 2.
6. `checkout(current_version)` is allowed and changes nothing. A negative
   or too-large version is `False`.
7. **Space:** the history should store compact add/remove operations, not
   full snapshots of the cart. A test builds a long history on a cart with
   thousands of distinct ingredients and checks out older versions within a
   time bound.

### Worked example

```python
recipes = {"A": {"egg": 2}, "B": {"egg": 2, "milk": 1}}
cart = Cart(recipes, {"egg": [(4, 3)]})
cart.add_recipe("A")          # version 1
cart.get_version()            # -> 1
cart.add_recipe("B")          # version 2
cart.get_total_discount()     # -> 3   (egg 4)
cart.checkout(1)              # -> True, version 2 is discarded
cart.get_version()            # -> 1
cart.get_total_discount()     # -> 0   (egg 2)
cart.checkout(2)              # -> False
```

### Clarifications

- **Does a failed `add_recipe` (unknown recipe) create a version?** No.
- **Does `checkout` create a version?** No.
- **Is version 0 reachable after later changes?** Yes: `checkout(0)` empties
  the cart.
- **What if I check out version 1, then add something, then check out
  version 2?** Version 2 is the new one created by that add.
- **Can I keep a full copy of the counts per version?** It would pass small
  tests but is exactly what the interviewer pushes back on. Store the
  operations and rebuild or reverse them. State the cost of `checkout`.

Run the provided tests with **Submit**; later parts come with their own test
files.

---
Interviewer notes

In the reports the interviewer insisted on a space-efficient history: store
(add, recipe) and (remove, recipe) operations, not snapshots, and replay or
undo them to reach a version. Graders also watch that checkout really
discards newer versions (a helper that truncates the log) and that version
numbers restart from the restored one. Be ready to state the time cost of
`checkout` and the memory cost of the log.

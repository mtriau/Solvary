# Recipe Shopping Cart: Part 3

The same `Cart` grows nested transactions, like a database: group several
changes, then keep them or throw them away. Part 1 and Part 2 tests still
run alongside the new ones.

### What to implement

- `begin() -> bool`: open a new transaction scope, nested inside any scope
  already open. Returns `True`, or `False` if 100 scopes are already open.
- `commit() -> bool`: close the innermost scope, keeping its changes.
  Returns `False` (doing nothing) if no scope is open.
- `abort() -> bool`: close the innermost scope and reverse every change made
  inside it. Returns `False` (doing nothing) if no scope is open.

### Rules

1. Scopes nest up to **depth 100**.
2. `get_total_discount()` and `ingredient_counts()` always see the current
   state, including changes in scopes that are still open.
3. `abort` reverses everything done inside that scope, **including the
   changes of inner scopes that were already committed**. An inner commit
   only hands its changes to the enclosing scope.
4. Aborting an inner scope leaves the enclosing scope's earlier changes in
   place.
5. **Versions:**
   - Mutations inside an open transaction do not create versions, and
     neither does an inner `commit`.
   - Committing the outermost scope creates **one** new version for the
     whole transaction, if at least one `add_recipe` or `remove_recipe`
     returned `True` inside it. An empty transaction creates none.
   - `abort` never creates a version.
   - `checkout` while any scope is open returns `False` and changes nothing.
6. A later `checkout` treats a committed transaction as one unit: going back
   past it undoes all of its changes, and restoring it applies all of them.

### Worked example

```python
cart = Cart({"A": {"egg": 2}, "B": {"egg": 2, "milk": 1}}, {"egg": [(4, 3)]})
cart.begin()
cart.add_recipe("A")
cart.begin()
cart.add_recipe("B")
cart.get_total_discount()   # -> 3   (uncommitted changes are visible)
cart.commit()               # -> True, B now belongs to the outer scope
cart.abort()                # -> True, A and B are both reversed
cart.ingredient_counts()    # -> {}
cart.commit()               # -> False, nothing is open
cart.get_version()          # -> 0
```

### Clarifications

- **`commit()` with nothing open?** `False`, no effect.
- **Can I `begin()` a 101st scope?** No, it returns `False`.
- **Does a transaction containing only failed calls make a version?** No.
- **Does an add followed by a remove of the same recipe inside a committed
  transaction make a version?** Yes: both were effective.
- **Is `checkout` allowed inside a transaction?** No; it returns `False`.
- **Do I snapshot at `begin`?** You can, but think about the cost with a
  deep stack; an undo log per scope is cheaper. State the trade-off.

Run the provided tests with **Submit**.

---
Interviewer notes

The core of this part is a stack of per-scope undo logs: abort replays the
inverse operations, and an inner commit merges its log into the parent so an
outer abort still reverses it. Graders check the matrix (inner commit then
outer abort, inner abort keeping outer changes, commit or abort with no
scope) and that the version rule is applied exactly. Comparing snapshot
and undo-log approaches out loud is the strong answer.

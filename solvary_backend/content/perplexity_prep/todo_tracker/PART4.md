# Agent Task Tracker: Part 4

`undo() -> bool`

Reverts the most recent successful mutating call: an `add`, a `set` that
returned `True`, or an `add_dependency` that changed something. The revert
includes every status change the call cascaded to other tasks.

- Returns `True` if something was undone, `False` if there is nothing to
  undo.
- Undoing an `add` removes the task; the next `add` reuses that id.
- Calls that failed or were no-ops (a `set` returning `False`, a no-op
  `add_dependency`, any call that raised) are not recorded and do not
  consume an undo.

Run the provided tests: `pytest todo_tracker -q`.

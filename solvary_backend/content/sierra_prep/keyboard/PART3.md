# Keyboard: Part 3

Add a cursor. Typing and deleting now happen at the cursor, and undo/redo
must restore the cursor too.

### What to implement

- `cursor() -> int`: the cursor position, from `0` (before the first
  character) to `len(text())` (after the last). A fresh keyboard has cursor
  `0`.
- `move_left(n: int = 1)`, `move_right(n: int = 1)`, `home()`, `end()`:
  move the cursor, clamped to the buffer.
- `delete(n: int = 1) -> None` (new): remove up to `n` characters **after**
  the cursor. The cursor does not move.

Existing methods change meaning:

- `type(s)` inserts `s` at the cursor and leaves the cursor just after the
  inserted text.
- `backspace(n)` removes up to `n` characters **before** the cursor and
  moves the cursor back by that many.

### Rules

1. **Cursor moves are not actions.** They are never undone on their own,
   and they do not clear the redo history.
2. `type`, `backspace` and `delete` are actions when they change the text,
   as in Part 2.
3. **`undo` restores both the text and the cursor** to what they were just
   before the action. **`redo` restores both** to what they were just after
   it. Any cursor movement that happened in between is discarded.

### Worked example

```python
kb = Keyboard()
kb.type("abc")       # "abc"  cursor 3
kb.move_left(1)      #        cursor 2
kb.type("X")         # "abXc" cursor 3
kb.home(); kb.delete()   # "bXc"  cursor 0
kb.undo()            # "abXc" cursor 0   (cursor as it was before delete)
kb.undo()            # "abc"  cursor 2
kb.redo()            # "abXc" cursor 3
```

### Clarifications

- **`backspace` with the cursor at 0?** Nothing is before the cursor, so
  nothing happens and it is not an action. Likewise `delete` with the cursor
  at the end.
- **`move_left(10)` with the cursor at 3?** Clamps to 0. `move_right` clamps
  to the length.
- **Type, undo, move around, then redo?** Redo still works (moves do not
  clear it) and puts the cursor where it was right after the original type.
- **Does a snapshot design still work?** Yes: the snapshot just becomes
  `(text, cursor)`. If you stored inverse operations instead, record the
  cursor on each action.
- **Does Part 1 and 2 behaviour still hold?** Yes. With the cursor at the
  end, `type` appends and `backspace` removes from the end, exactly as
  before.

Run the provided tests with **Submit**.

---
Interviewer notes

This is where a snapshot design pays off: the "state" simply grows a
cursor field. Inverse-operation designs need the cursor recorded on each
action. Check that `move_*` after an undo still allows a redo.

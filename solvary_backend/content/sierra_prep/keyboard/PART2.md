# Keyboard: Part 2

Add undo and redo.

### What to implement

- `undo() -> bool`: revert the most recent **action**. Return `True` if
  something was undone, `False` if there was nothing to undo.
- `redo() -> bool`: re-apply the most recently undone action. Return `True`
  if something was redone, `False` otherwise.

### Definitions and rules

1. **An action is one call to `type` or `backspace` that actually changed
   the text.** A multi-character `type("hello")` is a single action, and so
   is `backspace(3)`.
2. **No-ops are not actions:** `type("")`, `backspace(0)`, and `backspace`
   on an empty buffer. They are not recorded, so they cannot be undone, and
   they do not touch the redo history.
3. `undo` and `redo` are not actions themselves.
4. **A new action after an undo discards the redo history.** Once you type
   something new, the undone actions can no longer be redone.
5. Return actual booleans (`True` / `False`).

### Worked example

```python
kb = Keyboard()
kb.type("ab"); kb.type("cd"); kb.backspace()
kb.text()        # -> "abc"
kb.undo()        # -> True   text "abcd"
kb.undo()        # -> True   text "ab"
kb.redo()        # -> True   text "abcd"
kb.type("!")     #           text "abcd!"   (redo history gone)
kb.redo()        # -> False
kb.undo(); kb.undo(); kb.undo()   # -> True, True, True  text ""
kb.undo()        # -> False
```

### Clarifications

- **Does undoing `backspace(10)` on `"abc"` restore `"abc"`?** Yes. Exactly
  what was removed comes back, even though fewer than 10 characters went.
- **Several undos, then several redos?** Redo replays them in the original
  order: after undoing `1`, `2`, `3`, redo gives `"1"`, `"12"`, `"123"`.
- **A no-op after an undo. Is redo still possible?** Yes.
  `type("a"); undo(); type(""); backspace(); redo()` restores `"a"`.
- **`undo()` on a fresh keyboard?** `False`, and the text stays empty.
- **How much history?** A couple of thousand actions, and undo/redo should
  be cheap (not re-executing the whole history each time).
- **Snapshots or inverse operations?** Either works. Store the text before
  and after each action, or store what each action removed or added. Be
  ready to explain the choice.

Run the provided tests with **Submit**.

---
Interviewer notes

Two clean designs: snapshots (store the text before/after each action)
or inverse operations (store what was removed). Both are fine at this
scale; ask which they chose and why. The traps are counting no-ops as
actions and forgetting to clear the redo stack.

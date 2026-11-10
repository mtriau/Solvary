# Agent Task Tracker: Part 2

Dependencies now matter.

- A new task is `READY_TO_EXECUTE` if it has no deps or all of its deps are
  `SUCCEEDED`; otherwise it is `BLOCKED`. If any dep is already `FAILED`,
  the new task starts `FAILED` (`FAILED` wins over `BLOCKED`).
- When a task becomes `SUCCEEDED`, every `BLOCKED` task whose deps are now
  all `SUCCEEDED` becomes `READY_TO_EXECUTE`.
- When a task becomes `FAILED`, every task that depends on it directly or
  transitively becomes `FAILED`.
- `set()` can no longer move a task out of `BLOCKED` by hand: it returns
  `False` for any target status. The tracker owns that transition.

Example:

```python
t.add("a")            # -> 1 READY_TO_EXECUTE
t.add("b", [1])       # -> 2 BLOCKED
t.add("c", [1, 2])    # -> 3 BLOCKED
t.set(1, TaskStatus.IN_PROGRESS); t.set(1, TaskStatus.SUCCEEDED)
                      # 2 becomes READY_TO_EXECUTE, 3 still BLOCKED
t.set(2, TaskStatus.IN_PROGRESS); t.set(2, TaskStatus.FAILED)
                      # 3 becomes FAILED
```

Constraints: up to 200K operations, 100K adds, 200K dependency edges.

Run the provided tests: `pytest todo_tracker -q`.

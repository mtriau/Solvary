# Agent Task Tracker: Part 1

You are building the task list an AI agent uses to plan and track its own
work. Tasks have a status drawn from this ordered set (lowest to highest):

```
BLOCKED < READY_TO_EXECUTE < IN_PROGRESS < SUCCEEDED < FAILED
```

`SUCCEEDED` and `FAILED` are **terminal**.

`TaskStatus` is provided in the stub. Implement `ToDoList`:

- `add(description: str, deps: list[int] | None = None) -> int`
  Creates a task and returns its id. Ids are integers starting at `1`,
  increasing by one per add. `deps` is a list of ids of **existing** tasks.
  In this part, deps are stored and rendered but do not affect status: every
  new task starts `READY_TO_EXECUTE`.
- `get(task_id: int) -> str | None`
  Returns `"id|STATUS|description"`, or `None` if there is no such task.
- `set(task_id: int, new_status: TaskStatus) -> bool`
  Changes a task's status. Returns `True` only if the task exists, its
  current status is not terminal, and `new_status` is **strictly higher**
  than the current status. Otherwise returns `False` and changes nothing.
- `render() -> str`
  All tasks in id order, one per line, formatted
  `id|STATUS|deps|description` where deps is the comma-joined id list in
  the order given (empty field if no deps). Lines joined with `"\n"`.

```python
t = ToDoList()
t.add("write tests")                    # -> 1
t.add("ship", [1])                      # -> 2
t.get(2)                                # -> "2|READY_TO_EXECUTE|ship"
t.get(9)                                # -> None
t.set(1, TaskStatus.IN_PROGRESS)        # -> True
t.set(1, TaskStatus.READY_TO_EXECUTE)   # -> False  (not strictly higher)
t.set(9, TaskStatus.IN_PROGRESS)        # -> False  (no such task)
t.render()
# "1|IN_PROGRESS||write tests\n2|READY_TO_EXECUTE|1|ship"
```

Error contract:

- `add` with a dep id that does not exist raises `ValueError` and creates
  nothing (the next id is unchanged).
- Duplicate ids in `deps` are kept as given and rendered as given.
- `set` to the same status returns `False`. Jumps to any strictly higher
  status return `True` (`READY_TO_EXECUTE -> FAILED` is `True`).
- Status rendering uses the enum NAME (`READY_TO_EXECUTE`, not `1`).
- `render()` on an empty list returns `""`.

Run the provided tests: `pytest todo_tracker -q`. Later parts come with
their own test files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

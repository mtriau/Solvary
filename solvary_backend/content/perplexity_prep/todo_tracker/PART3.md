# Agent Task Tracker: Part 3

`add_dependency(task_id: int, dep_id: int) -> None`

Adds `dep_id` as a dependency of an existing task.

- Unknown `task_id` or `dep_id`: raise `ValueError`.
- If `dep_id` is already a dependency of `task_id`: no-op (nothing appended,
  nothing raised).
- Tasks that are `IN_PROGRESS` or terminal cannot gain dependencies: raise
  `ValueError`, change nothing.
- If this would create a cycle, raise `ValueError` whose message contains
  the cycle as a path of ids, starting and ending at `task_id` and following
  dependency direction `task_id -> dep_id -> ... -> task_id` (for example
  `[2, 3, 2]`). Change nothing: deps, dependents, statuses all untouched.
  A self dependency `add_dependency(3, 3)` is the cycle `[3, 3]`.
- After a successful add: if the new dep is `FAILED`, the task becomes
  `FAILED` and that cascades to its dependents. Otherwise, if the task is
  `READY_TO_EXECUTE` and the new dep is not `SUCCEEDED`, the task becomes
  `BLOCKED`. A `BLOCKED` task gaining a `SUCCEEDED` dep stays `BLOCKED`.

Run the provided tests: `pytest todo_tracker -q`.

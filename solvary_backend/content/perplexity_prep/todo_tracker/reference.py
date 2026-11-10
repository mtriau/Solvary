"""Ideal solution: Agent Task Tracker, all four parts.

Part 1: add / get / set / render. Ids start at 1; set() only moves a task
        strictly up the status order and never out of a terminal state.
Part 2: dependency resolution. A new task is BLOCKED while any dep is not
        SUCCEEDED (FAILED if any dep is FAILED). Succeeding a task wakes the
        BLOCKED dependents whose deps are now all SUCCEEDED; failing a task
        fails every transitive dependent. set() cannot move a BLOCKED task.
Part 3: add_dependency(task_id, dep_id). Cycle check is an iterative search
        from dep_id along deps edges; reaching task_id means a cycle, and the
        path is rebuilt from a parent map. Nothing is written before the
        check passes.
Part 4: undo(). Every successful mutating call pushes one record holding
        its structural inverse plus every (task_id, old_status) it touched,
        cascades included. Calls that raise or return False push nothing.

Shape an interviewer expects:
  - Two adjacency maps, both maintained at write time: `deps[id]` (the
    list the task was given, in order) and `dependents[id]` (who is
    waiting on id). Rebuilding dependents by scanning all tasks on every
    set() would be O(V) per call and too slow at 200K ops.
  - Cascades are iterative (explicit stack plus a visited set). A 5000-deep
    chain kills recursion in CPython.
  - set() is the single entry point for transitions; _on_succeeded and
    _on_failed are private, idempotent, and return the list of status
    changes they made so undo can revert them.
"""

from collections import defaultdict
from enum import Enum


class TaskStatus(Enum):
    BLOCKED = 0
    READY_TO_EXECUTE = 1
    IN_PROGRESS = 2
    SUCCEEDED = 3
    FAILED = 4


TERMINAL = {TaskStatus.SUCCEEDED, TaskStatus.FAILED}


class _Task:
    __slots__ = ("id", "description", "deps", "status")

    def __init__(self, task_id: int, description: str, deps: list[int]) -> None:
        self.id = task_id
        self.description = description
        self.deps = deps
        self.status = TaskStatus.READY_TO_EXECUTE


class ToDoList:
    def __init__(self) -> None:
        self._tasks: dict[int, _Task] = {}
        self._dependents: dict[int, list[int]] = defaultdict(list)
        self._next_id = 1
        # Undo log. Each entry is a tuple whose first element names the op.
        #   ("add", task_id)
        #   ("set", changes)                         changes: list[(id, old)]
        #   ("add_dependency", task_id, dep_id, changes)
        self._history: list[tuple] = []

    # ------------------------------------------------------------ Part 1

    def add(self, description: str, deps: list[int] | None = None) -> int:
        deps = list(deps) if deps else []
        for d in deps:
            if d not in self._tasks:
                raise ValueError(f"unknown dependency id {d}")
        task_id = self._next_id
        task = _Task(task_id, description, deps)
        task.status = self._initial_status(deps)
        self._tasks[task_id] = task
        for d in dict.fromkeys(deps):          # dedupe, keep order
            self._dependents[d].append(task_id)
        self._next_id += 1
        self._history.append(("add", task_id))
        return task_id

    def get(self, task_id: int) -> str | None:
        task = self._tasks.get(task_id)
        if task is None:
            return None
        return f"{task.id}|{task.status.name}|{task.description}"

    def set(self, task_id: int, new_status: TaskStatus) -> bool:
        task = self._tasks.get(task_id)
        if task is None:
            return False
        if task.status in TERMINAL or task.status is TaskStatus.BLOCKED:
            return False
        if new_status.value <= task.status.value:
            return False
        changes = [(task_id, task.status)]
        task.status = new_status
        if new_status is TaskStatus.SUCCEEDED:
            changes.extend(self._on_succeeded(task_id))
        elif new_status is TaskStatus.FAILED:
            changes.extend(self._on_failed(task_id))
        self._history.append(("set", changes))
        return True

    def render(self) -> str:
        lines = []
        for task_id in sorted(self._tasks):
            task = self._tasks[task_id]
            deps = ",".join(str(d) for d in task.deps)
            lines.append(f"{task.id}|{task.status.name}|{deps}|{task.description}")
        return "\n".join(lines)

    # ------------------------------------------------------------ Part 2

    def _initial_status(self, deps: list[int]) -> TaskStatus:
        statuses = [self._tasks[d].status for d in deps]
        if any(s is TaskStatus.FAILED for s in statuses):
            return TaskStatus.FAILED
        if all(s is TaskStatus.SUCCEEDED for s in statuses):
            return TaskStatus.READY_TO_EXECUTE
        return TaskStatus.BLOCKED

    def _all_deps_succeeded(self, task_id: int) -> bool:
        return all(
            self._tasks[d].status is TaskStatus.SUCCEEDED
            for d in self._tasks[task_id].deps
        )

    def _on_succeeded(self, task_id: int) -> list[tuple[int, TaskStatus]]:
        # READY_TO_EXECUTE unblocks nobody further, so one level is enough.
        changes = []
        for dep_id in self._dependents.get(task_id, ()):
            dependent = self._tasks[dep_id]
            if dependent.status is TaskStatus.BLOCKED and self._all_deps_succeeded(dep_id):
                changes.append((dep_id, dependent.status))
                dependent.status = TaskStatus.READY_TO_EXECUTE
        return changes

    def _on_failed(self, task_id: int) -> list[tuple[int, TaskStatus]]:
        # Iterative DFS with a visited set: a 5000-deep chain and a diamond
        # both terminate in O(V + E) with every node written at most once.
        changes = []
        stack = [task_id]
        seen = {task_id}
        while stack:
            current = stack.pop()
            for dep_id in self._dependents.get(current, ()):
                if dep_id in seen:
                    continue
                seen.add(dep_id)
                dependent = self._tasks[dep_id]
                if dependent.status is not TaskStatus.FAILED:
                    changes.append((dep_id, dependent.status))
                    dependent.status = TaskStatus.FAILED
                stack.append(dep_id)
        return changes

    # ------------------------------------------------------------ Part 3

    def add_dependency(self, task_id: int, dep_id: int) -> None:
        if task_id not in self._tasks or dep_id not in self._tasks:
            raise ValueError(f"unknown task id in ({task_id}, {dep_id})")
        task = self._tasks[task_id]
        if dep_id in task.deps:
            return
        if task.status is TaskStatus.IN_PROGRESS or task.status in TERMINAL:
            raise ValueError(
                f"task {task_id} is {task.status.name} and cannot gain dependencies"
            )
        cycle = self._find_cycle(task_id, dep_id)
        if cycle is not None:
            raise ValueError(f"adding dependency would create a cycle: {cycle}")

        # Validation passed: now write, and record everything for undo.
        task.deps.append(dep_id)
        self._dependents[dep_id].append(task_id)
        changes: list[tuple[int, TaskStatus]] = []
        dep_status = self._tasks[dep_id].status
        if dep_status is TaskStatus.FAILED:
            changes.append((task_id, task.status))
            task.status = TaskStatus.FAILED
            changes.extend(self._on_failed(task_id))
        elif task.status is TaskStatus.READY_TO_EXECUTE and dep_status is not TaskStatus.SUCCEEDED:
            changes.append((task_id, task.status))
            task.status = TaskStatus.BLOCKED
        self._history.append(("add_dependency", task_id, dep_id, changes))

    def _find_cycle(self, task_id: int, dep_id: int) -> list[int] | None:
        """Walk deps edges from dep_id. Reaching task_id closes a cycle.

        Searching from dep_id means the path we rebuild is exactly the
        dependency walk task_id -> dep_id -> ... -> task_id, which is what
        the error message should show.
        """
        if dep_id == task_id:
            return [task_id, task_id]
        parent = {dep_id: None}
        stack = [dep_id]
        while stack:
            current = stack.pop()
            for nxt in self._tasks[current].deps:
                if nxt in parent:
                    continue
                parent[nxt] = current
                if nxt == task_id:
                    path = []
                    node = nxt
                    while node is not None:
                        path.append(node)
                        node = parent[node]
                    path.reverse()               # dep_id ... task_id
                    return [task_id] + path
                stack.append(nxt)
        return None

    # ------------------------------------------------------------ Part 4

    def undo(self) -> bool:
        if not self._history:
            return False
        record = self._history.pop()
        kind = record[0]
        if kind == "add":
            task_id = record[1]
            task = self._tasks.pop(task_id)
            for d in dict.fromkeys(task.deps):
                self._dependents[d].remove(task_id)
            self._dependents.pop(task_id, None)
            self._next_id = task_id
        elif kind == "set":
            self._restore(record[1])
        else:  # add_dependency
            _, task_id, dep_id, changes = record
            self._tasks[task_id].deps.remove(dep_id)
            self._dependents[dep_id].remove(task_id)
            self._restore(changes)
        return True

    def _restore(self, changes: list[tuple[int, TaskStatus]]) -> None:
        for task_id, old_status in reversed(changes):
            self._tasks[task_id].status = old_status


if __name__ == "__main__":
    S = TaskStatus
    t = ToDoList()
    assert t.add("a") == 1
    assert t.add("b", [1]) == 2
    assert t.add("c", [1, 2]) == 3
    assert t.get(2) == "2|BLOCKED|b"
    assert t.set(1, S.IN_PROGRESS) and t.set(1, S.SUCCEEDED)
    assert t.get(2) == "2|READY_TO_EXECUTE|b" and t.get(3) == "3|BLOCKED|c"
    assert t.set(2, S.IN_PROGRESS) and t.set(2, S.FAILED)
    assert t.get(3) == "3|FAILED|c"
    assert t.undo() and t.get(3) == "3|BLOCKED|c" and t.get(2) == "2|IN_PROGRESS|b"

    t = ToDoList()
    for i in range(1, 5):
        t.add(f"t{i}", [i - 1] if i > 1 else None)
    try:
        t.add_dependency(2, 4)
    except ValueError as e:
        assert "[2, 4, 3, 2]" in str(e)
    else:
        raise AssertionError("cycle not detected")
    assert t.render().splitlines()[1] == "2|BLOCKED|1|t2"

    t = ToDoList()
    t.add("root")
    for i in range(2, 5001):
        t.add(f"t{i}", [i - 1])
    assert t.set(1, S.IN_PROGRESS) and t.set(1, S.FAILED)
    assert t.get(5000) == "5000|FAILED|t5000"
    assert t.undo() and t.get(5000) == "5000|BLOCKED|t5000"
    print("OK")

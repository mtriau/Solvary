"""Part 4 provided tests: undo.

Run with: pytest todo_tracker -q
"""

import pytest

from todo_tracker import TaskStatus, ToDoList

S = TaskStatus


def _finish(t: ToDoList, task_id: int) -> None:
    assert t.set(task_id, S.IN_PROGRESS) is True
    assert t.set(task_id, S.SUCCEEDED) is True


def _fail(t: ToDoList, task_id: int) -> None:
    assert t.set(task_id, S.IN_PROGRESS) is True
    assert t.set(task_id, S.FAILED) is True


def _status(t: ToDoList, task_id: int) -> str:
    return t.get(task_id).split("|")[1]


# ------------------------------------------------------------ basics

def test_undo_with_nothing_to_undo_returns_false():
    t = ToDoList()
    assert t.undo() is False
    assert t.render() == ""


def test_undo_returns_true_when_something_was_undone():
    t = ToDoList()
    t.add("a")
    assert t.undo() is True


def test_undo_add_removes_task():
    t = ToDoList()
    t.add("a")
    t.add("b")
    assert t.undo() is True
    assert t.get(2) is None
    assert t.render() == "1|READY_TO_EXECUTE||a"


def test_undo_add_reuses_next_id():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.undo()
    assert t.add("c") == 2
    assert t.get(2) == "2|READY_TO_EXECUTE|c"


def test_undo_add_removes_task_from_dependents_of_its_deps():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.undo()
    t.add("c")                    # reuses id 2, no deps
    _fail(t, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"


def test_undo_all_adds_returns_to_empty_then_false():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [2])
    assert t.undo() is True
    assert t.undo() is True
    assert t.undo() is True
    assert t.render() == ""
    assert t.undo() is False
    assert t.add("fresh") == 1


# ------------------------------------------------------------ set

def test_undo_set_restores_status():
    t = ToDoList()
    t.add("a")
    t.set(1, S.IN_PROGRESS)
    assert t.undo() is True
    assert _status(t, 1) == "READY_TO_EXECUTE"


def test_undo_set_restores_terminal_to_previous_status():
    t = ToDoList()
    t.add("a")
    _finish(t, 1)
    assert t.undo() is True
    assert _status(t, 1) == "IN_PROGRESS"
    assert t.set(1, S.FAILED) is True


def test_undo_set_restores_cascaded_unblocks():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [1])
    _finish(t, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"
    assert t.undo() is True
    assert _status(t, 1) == "IN_PROGRESS"
    assert _status(t, 2) == "BLOCKED"
    assert _status(t, 3) == "BLOCKED"


def test_undo_set_restores_cascaded_failures():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [2])
    _fail(t, 1)
    assert t.undo() is True
    assert _status(t, 1) == "IN_PROGRESS"
    assert _status(t, 2) == "BLOCKED"
    assert _status(t, 3) == "BLOCKED"


def test_undo_diamond_failure_restores_every_node():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [1])
    t.add("d", [2, 3])
    before = t.render()
    assert t.set(1, S.FAILED) is True
    assert t.undo() is True
    assert t.render() == before


def test_undo_set_does_not_touch_tasks_that_were_already_failed():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c", [1, 2])
    _fail(t, 2)                   # 3 FAILED here
    _fail(t, 1)                   # 3 already FAILED, must not be recorded
    assert t.undo() is True
    assert _status(t, 1) == "IN_PROGRESS"
    assert _status(t, 3) == "FAILED"


def test_rejected_set_does_not_consume_an_undo():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.IN_PROGRESS) is True
    assert t.set(1, S.READY_TO_EXECUTE) is False
    assert t.set(9, S.FAILED) is False
    assert t.undo() is True
    assert _status(t, 1) == "READY_TO_EXECUTE"
    assert t.undo() is True
    assert t.render() == ""


def test_set_on_blocked_task_does_not_consume_an_undo():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    assert t.set(2, S.IN_PROGRESS) is False
    assert t.undo() is True
    assert t.get(2) is None


# ------------------------------------------------------------ add_dependency

def test_undo_add_dependency_removes_edge_and_restores_status():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add_dependency(2, 1)
    assert _status(t, 2) == "BLOCKED"
    assert t.undo() is True
    assert t.render() == "1|READY_TO_EXECUTE||a\n2|READY_TO_EXECUTE||b"


def test_undo_add_dependency_removes_dependent_edge():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add_dependency(2, 1)
    t.undo()
    _fail(t, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"


def test_undo_add_dependency_restores_failure_cascade():
    t = ToDoList()
    t.add("failed")
    t.add("b")
    t.add("c", [2])
    _fail(t, 1)
    t.add_dependency(2, 1)
    assert _status(t, 2) == "FAILED"
    assert _status(t, 3) == "FAILED"
    assert t.undo() is True
    assert _status(t, 2) == "READY_TO_EXECUTE"
    assert _status(t, 3) == "BLOCKED"
    assert t.render().splitlines()[1] == "2|READY_TO_EXECUTE||b"


def test_undo_add_dependency_keeps_earlier_deps():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c", [1])
    t.add_dependency(3, 2)
    t.undo()
    assert t.render().splitlines()[2] == "3|BLOCKED|1|c"


def test_noop_add_dependency_does_not_consume_an_undo():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add_dependency(2, 1)        # already a dep: no-op
    assert t.undo() is True
    assert t.get(2) is None


def test_raising_add_dependency_does_not_consume_an_undo():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    with pytest.raises(ValueError):
        t.add_dependency(1, 2)    # cycle
    with pytest.raises(ValueError):
        t.add_dependency(1, 9)    # unknown
    assert t.undo() is True
    assert t.get(2) is None
    assert t.render() == "1|READY_TO_EXECUTE||a"


def test_raising_add_does_not_consume_an_undo():
    t = ToDoList()
    t.add("a")
    with pytest.raises(ValueError):
        t.add("b", [9])
    assert t.undo() is True
    assert t.render() == ""


# ------------------------------------------------------------ sequences

def test_multiple_undos_rewind_in_reverse_order():
    t = ToDoList()
    t.add("a")                                # op 1
    t.add("b", [1])                           # op 2
    _finish(t, 1)                             # ops 3, 4 (unblocks 2)
    t.set(2, S.IN_PROGRESS)                   # op 5
    assert t.undo() is True
    assert _status(t, 2) == "READY_TO_EXECUTE"
    assert t.undo() is True
    assert _status(t, 1) == "IN_PROGRESS" and _status(t, 2) == "BLOCKED"
    assert t.undo() is True
    assert _status(t, 1) == "READY_TO_EXECUTE"
    assert t.undo() is True
    assert t.get(2) is None
    assert t.undo() is True
    assert t.render() == ""
    assert t.undo() is False


def test_new_ops_after_undo_are_undone_first():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.undo()                                  # removes b
    t.add("c")                                # id 2
    t.set(2, S.IN_PROGRESS)
    assert t.undo() is True
    assert t.get(2) == "2|READY_TO_EXECUTE|c"
    assert t.undo() is True
    assert t.get(2) is None
    assert t.undo() is True
    assert t.render() == ""


def test_undo_long_chain_cascade_restores_every_task():
    t = ToDoList()
    t.add("t1")
    for i in range(2, 5001):
        t.add(f"t{i}", [i - 1])
    before = t.render()
    assert t.set(1, S.FAILED) is True
    assert _status(t, 5000) == "FAILED"
    assert t.undo() is True
    assert t.render() == before

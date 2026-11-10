"""Part 3 provided tests: add_dependency and cycle detection.

Run with: pytest todo_tracker -q
"""

import time

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


def _deps(t: ToDoList, task_id: int) -> str:
    return t.render().splitlines()[task_id - 1].split("|")[2]


# ------------------------------------------------------------ validation

def test_add_dependency_unknown_task_raises_value_error():
    t = ToDoList()
    t.add("a")
    with pytest.raises(ValueError):
        t.add_dependency(9, 1)


def test_add_dependency_unknown_dep_raises_value_error():
    t = ToDoList()
    t.add("a")
    with pytest.raises(ValueError):
        t.add_dependency(1, 9)
    assert t.render() == "1|READY_TO_EXECUTE||a"


def test_add_dependency_returns_none_and_appends_dep_in_order():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c", [2])
    assert t.add_dependency(3, 1) is None
    assert _deps(t, 3) == "2,1"


def test_add_dependency_existing_dep_is_noop():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    assert t.add_dependency(2, 1) is None
    assert _deps(t, 2) == "1"
    assert _status(t, 2) == "BLOCKED"


def test_add_dependency_on_in_progress_task_raises():
    t = ToDoList()
    t.add("a")
    t.add("b")
    assert t.set(1, S.IN_PROGRESS) is True
    with pytest.raises(ValueError):
        t.add_dependency(1, 2)


def test_add_dependency_on_succeeded_task_raises():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    with pytest.raises(ValueError):
        t.add_dependency(1, 2)


def test_add_dependency_on_failed_task_raises():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _fail(t, 1)
    with pytest.raises(ValueError):
        t.add_dependency(1, 2)


def test_add_dependency_status_rejection_changes_nothing():
    t = ToDoList()
    t.add("a")
    t.add("b")
    assert t.set(1, S.IN_PROGRESS) is True
    with pytest.raises(ValueError):
        t.add_dependency(1, 2)
    assert t.render() == "1|IN_PROGRESS||a\n2|READY_TO_EXECUTE||b"
    # 2 must not have picked up 1 as a dependent either.
    _fail(t, 2)
    assert _status(t, 1) == "IN_PROGRESS"


# ------------------------------------------------------------ cycles

def test_two_node_cycle_message_lists_path():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    with pytest.raises(ValueError) as exc:
        t.add_dependency(1, 2)
    assert "[1, 2, 1]" in str(exc.value)


def test_self_dependency_is_a_cycle():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c")
    with pytest.raises(ValueError) as exc:
        t.add_dependency(3, 3)
    assert "[3, 3]" in str(exc.value)
    assert _deps(t, 3) == ""


def test_three_node_cycle_path_is_a_real_walk():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [2])
    with pytest.raises(ValueError) as exc:
        t.add_dependency(1, 3)
    assert "[1, 3, 2, 1]" in str(exc.value)


def test_cycle_path_follows_dependency_direction_from_task_to_dep():
    t = ToDoList()
    t.add("t1")
    t.add("t2", [1])
    t.add("t3", [2])
    t.add("t4", [3])
    with pytest.raises(ValueError) as exc:
        t.add_dependency(2, 4)
    assert "[2, 4, 3, 2]" in str(exc.value)


def test_cycle_error_leaves_deps_dependents_and_statuses_untouched():
    # 1 <- 2 <- 3, and 3 also depends on side task 5. add_dependency(1, 3)
    # is a cycle. If the implementation wrote deps[1] or dependents[3]
    # before raising, failing 5 would drag 1 (and then 2) down with 3.
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [2])
    t.add("unrelated")
    t.add("side")
    t.add_dependency(3, 5)
    before = t.render()
    with pytest.raises(ValueError) as exc:
        t.add_dependency(1, 3)
    assert "[1, 3, 2, 1]" in str(exc.value)
    assert t.render() == before
    assert _status(t, 1) == "READY_TO_EXECUTE"
    # Raising again (not a no-op) proves deps[1] did not gain 3.
    with pytest.raises(ValueError):
        t.add_dependency(1, 3)
    _fail(t, 5)
    assert _status(t, 3) == "FAILED"
    assert _status(t, 1) == "READY_TO_EXECUTE"
    assert _status(t, 2) == "BLOCKED"


def test_no_cycle_when_dep_is_an_ancestor_sibling():
    # 1 <- 2 and 1 <- 3; making 3 depend on 2 is a DAG, not a cycle.
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [1])
    t.add_dependency(3, 2)
    assert _deps(t, 3) == "1,2"


# ------------------------------------------------------------ status effects

def test_ready_task_gains_unfinished_dep_becomes_blocked():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add_dependency(2, 1)
    assert _status(t, 2) == "BLOCKED"
    assert _deps(t, 2) == "1"


def test_ready_task_gains_in_progress_dep_becomes_blocked():
    t = ToDoList()
    t.add("a")
    t.add("b")
    assert t.set(1, S.IN_PROGRESS) is True
    t.add_dependency(2, 1)
    assert _status(t, 2) == "BLOCKED"


def test_ready_task_gains_succeeded_dep_stays_ready():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    t.add_dependency(2, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"
    assert _deps(t, 2) == "1"


def test_blocked_task_gains_succeeded_dep_stays_blocked():
    t = ToDoList()
    t.add("a")
    t.add("done")
    t.add("c", [1])
    _finish(t, 2)
    t.add_dependency(3, 2)
    assert _status(t, 3) == "BLOCKED"
    assert _deps(t, 3) == "1,2"


def test_blocked_task_gains_unfinished_dep_and_unblocks_only_when_both_succeed():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c", [1])
    t.add_dependency(3, 2)
    _finish(t, 1)
    assert _status(t, 3) == "BLOCKED"
    _finish(t, 2)
    assert _status(t, 3) == "READY_TO_EXECUTE"


def test_task_gains_failed_dep_becomes_failed_and_cascades():
    t = ToDoList()
    t.add("failed")
    t.add("b")
    t.add("c", [2])
    t.add("d", [3])
    _fail(t, 1)
    t.add_dependency(2, 1)
    assert [_status(t, i) for i in (2, 3, 4)] == ["FAILED"] * 3
    assert _deps(t, 2) == "1"


def test_new_dep_participates_in_later_failure_cascade():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c", [2])
    t.add_dependency(2, 1)
    _fail(t, 1)
    assert _status(t, 2) == "FAILED"
    assert _status(t, 3) == "FAILED"


# ------------------------------------------------------------ scale

def test_deep_chain_cycle_check_is_iterative():
    t = ToDoList()
    t.add("t1")
    for i in range(2, 5001):
        t.add(f"t{i}", [i - 1])
    start = time.perf_counter()
    with pytest.raises(ValueError) as exc:
        t.add_dependency(1, 5000)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"cycle check took {elapsed:.2f}s"
    expected = [1] + list(range(5000, 0, -1))
    assert str(expected) in str(exc.value)
    assert _deps(t, 1) == ""


def test_deep_chain_without_cycle_adds_dependency():
    t = ToDoList()
    t.add("t1")
    for i in range(2, 5001):
        t.add(f"t{i}", [i - 1])
    t.add("side")
    start = time.perf_counter()
    t.add_dependency(5001, 5000)      # walks 5000 deep, never reaches 5001
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"cycle check took {elapsed:.2f}s"
    assert _status(t, 5001) == "BLOCKED"
    assert _deps(t, 5001) == "5000"

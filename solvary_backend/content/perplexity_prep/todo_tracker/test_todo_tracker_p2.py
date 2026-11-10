"""Part 2 provided tests: dependency resolution and cascades.

Run with: pytest todo_tracker -q
"""

import time

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


# ------------------------------------------------------------ status at add

def test_new_task_with_no_deps_is_ready():
    t = ToDoList()
    t.add("a")
    assert _status(t, 1) == "READY_TO_EXECUTE"


def test_new_task_with_unfinished_dep_is_blocked():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    assert _status(t, 2) == "BLOCKED"


def test_new_task_whose_deps_all_succeeded_is_ready():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    _finish(t, 2)
    t.add("c", [1, 2])
    assert _status(t, 3) == "READY_TO_EXECUTE"


def test_new_task_with_mixed_succeeded_and_unfinished_deps_is_blocked():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    t.add("c", [1, 2])
    assert _status(t, 3) == "BLOCKED"


def test_new_task_with_failed_dep_starts_failed():
    t = ToDoList()
    t.add("a")
    _fail(t, 1)
    t.add("b", [1])
    assert _status(t, 2) == "FAILED"


def test_failed_dep_wins_over_blocked_when_deps_are_mixed():
    t = ToDoList()
    t.add("ready")
    t.add("failed")
    _fail(t, 2)
    t.add("x", [1, 2])
    t.add("y", [2, 1])
    assert _status(t, 3) == "FAILED"
    assert _status(t, 4) == "FAILED"


# ------------------------------------------------------------ spec example

def test_spec_example_sequence():
    t = ToDoList()
    assert t.add("a") == 1
    assert t.add("b", [1]) == 2
    assert t.add("c", [1, 2]) == 3
    assert t.render() == (
        "1|READY_TO_EXECUTE||a\n2|BLOCKED|1|b\n3|BLOCKED|1,2|c"
    )
    _finish(t, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"
    assert _status(t, 3) == "BLOCKED"
    _fail(t, 2)
    assert _status(t, 3) == "FAILED"


# ------------------------------------------------------------ unblocking

def test_succeed_unblocks_dependent_when_all_deps_succeeded():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    _finish(t, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"


def test_succeed_does_not_unblock_dependent_with_other_unfinished_dep():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.add("c", [1, 2])
    _finish(t, 1)
    assert _status(t, 3) == "BLOCKED"
    _finish(t, 2)
    assert _status(t, 3) == "READY_TO_EXECUTE"


def test_succeed_unblocks_every_direct_dependent():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [1])
    t.add("d", [1])
    _finish(t, 1)
    assert [_status(t, i) for i in (2, 3, 4)] == ["READY_TO_EXECUTE"] * 3


def test_in_progress_dep_does_not_unblock():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    assert t.set(1, S.IN_PROGRESS) is True
    assert _status(t, 2) == "BLOCKED"


def test_unblocked_task_can_then_progress_and_unblock_the_next():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [2])
    _finish(t, 1)
    _finish(t, 2)
    assert _status(t, 3) == "READY_TO_EXECUTE"


def test_unblock_requires_all_deps_check_not_a_counter():
    # Dep 1 succeeded BEFORE the task was added; only dep 2 is outstanding.
    # A counter initialised from len(deps) or decremented on every success
    # gets this wrong.
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    t.add("c", [1, 2])
    assert _status(t, 3) == "BLOCKED"
    _finish(t, 2)
    assert _status(t, 3) == "READY_TO_EXECUTE"


def test_duplicate_deps_do_not_double_count_unblock():
    t = ToDoList()
    t.add("a")
    t.add("b", [1, 1])
    assert _status(t, 2) == "BLOCKED"
    _finish(t, 1)
    assert _status(t, 2) == "READY_TO_EXECUTE"
    assert t.render().splitlines()[1] == "2|READY_TO_EXECUTE|1,1|b"


def test_succeed_task_with_no_dependents_does_not_crash():
    t = ToDoList()
    t.add("lonely")
    _finish(t, 1)
    assert t.render() == "1|SUCCEEDED||lonely"


# ------------------------------------------------------------ set on BLOCKED

def test_set_on_blocked_task_returns_false_for_every_target():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    for target in (S.BLOCKED, S.READY_TO_EXECUTE, S.IN_PROGRESS, S.SUCCEEDED, S.FAILED):
        assert t.set(2, target) is False
    assert _status(t, 2) == "BLOCKED"


def test_failed_dependent_cannot_be_set_succeeded():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    _fail(t, 1)
    assert _status(t, 2) == "FAILED"
    assert t.set(2, S.SUCCEEDED) is False
    assert _status(t, 2) == "FAILED"


# ------------------------------------------------------------ failure cascade

def test_fail_cascades_to_direct_dependents():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [1])
    _fail(t, 1)
    assert _status(t, 2) == "FAILED"
    assert _status(t, 3) == "FAILED"


def test_fail_cascades_transitively():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [2])
    t.add("d", [3])
    _fail(t, 1)
    assert [_status(t, i) for i in (1, 2, 3, 4)] == ["FAILED"] * 4


def test_fail_cascade_marks_shared_descendant_once():
    # Diamond: 1 <- 2, 1 <- 3, {2, 3} <- 4. Task 4 is reachable twice.
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("c", [1])
    t.add("d", [2, 3])
    _fail(t, 1)
    assert t.render() == (
        "1|FAILED||a\n2|FAILED|1|b\n3|FAILED|1|c\n4|FAILED|2,3|d"
    )


def test_fail_cascade_leaves_unrelated_tasks_untouched():
    t = ToDoList()
    t.add("a")
    t.add("b", [1])
    t.add("other")
    t.add("other child", [3])
    _fail(t, 1)
    assert _status(t, 3) == "READY_TO_EXECUTE"
    assert _status(t, 4) == "BLOCKED"


def test_fail_cascade_does_not_touch_succeeded_siblings():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    t.add("c", [1, 2])
    _fail(t, 2)
    assert _status(t, 1) == "SUCCEEDED"
    assert _status(t, 3) == "FAILED"


# ------------------------------------------------------------ scale

def test_long_chain_cascade_is_iterative():
    t = ToDoList()
    t.add("t1")
    for i in range(2, 5001):
        t.add(f"t{i}", [i - 1])
    _fail(t, 1)          # recursion dies around 1000 deep
    assert _status(t, 5000) == "FAILED"
    assert _status(t, 2500) == "FAILED"


def test_wide_lattice_fail_cascade_completes_quickly():
    # Root plus 25 layers of 2 tasks, each depending on both tasks of the
    # previous layer: 2^25 paths without a visited set.
    t = ToDoList()
    root = t.add("root")
    prev = [root]
    for layer in range(25):
        cur = [t.add(f"L{layer}a", list(prev)), t.add(f"L{layer}b", list(prev))]
        prev = cur
    start = time.perf_counter()
    _fail(t, root)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"cascade took {elapsed:.2f}s"
    assert all(_status(t, i) == "FAILED" for i in prev)


def test_wide_lattice_success_waves_unblock_layer_by_layer():
    t = ToDoList()
    root = t.add("root")
    layers = []
    prev = [root]
    for layer in range(25):
        cur = [t.add(f"L{layer}a", list(prev)), t.add(f"L{layer}b", list(prev))]
        layers.append(cur)
        prev = cur
    start = time.perf_counter()
    _finish(t, root)
    for i, layer in enumerate(layers):
        assert [_status(t, x) for x in layer] == ["READY_TO_EXECUTE"] * 2
        if i + 1 < len(layers):
            assert [_status(t, x) for x in layers[i + 1]] == ["BLOCKED"] * 2
        for x in layer:
            _finish(t, x)
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"unblocking took {elapsed:.2f}s"

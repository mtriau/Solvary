"""Part 1 provided tests: add / get / set / render.

Run with: pytest todo_tracker -q
"""

import pytest

from todo_tracker import TaskStatus, ToDoList

S = TaskStatus


def _finish(t: ToDoList, task_id: int) -> None:
    """Drive a READY task to SUCCEEDED through the public API."""
    assert t.set(task_id, S.IN_PROGRESS) is True
    assert t.set(task_id, S.SUCCEEDED) is True


# ------------------------------------------------------------------ add / get

def test_add_returns_sequential_ids_starting_at_one():
    t = ToDoList()
    assert t.add("a") == 1
    assert t.add("b") == 2
    assert t.add("c") == 3


def test_get_formats_id_status_description():
    t = ToDoList()
    t.add("write tests")
    assert t.get(1) == "1|READY_TO_EXECUTE|write tests"


def test_get_unknown_id_returns_none():
    t = ToDoList()
    t.add("a")
    assert t.get(9) is None
    assert t.get(0) is None


def test_new_task_without_deps_starts_ready_to_execute():
    t = ToDoList()
    t.add("a")
    t.add("b", [])
    assert t.get(1) == "1|READY_TO_EXECUTE|a"
    assert t.get(2) == "2|READY_TO_EXECUTE|b"


def test_add_with_empty_deps_list_matches_none():
    t = ToDoList()
    t.add("a", None)
    t.add("b", [])
    assert t.render() == "1|READY_TO_EXECUTE||a\n2|READY_TO_EXECUTE||b"


def test_add_with_unknown_dep_raises_value_error():
    t = ToDoList()
    t.add("a")
    with pytest.raises(ValueError):
        t.add("b", [7])


def test_add_with_unknown_dep_creates_nothing_and_next_id_is_unchanged():
    t = ToDoList()
    t.add("a")
    with pytest.raises(ValueError):
        t.add("b", [7])
    assert t.get(2) is None
    assert t.render() == "1|READY_TO_EXECUTE||a"
    assert t.add("c") == 2


def test_add_with_mixed_known_and_unknown_deps_creates_nothing():
    t = ToDoList()
    t.add("a")
    with pytest.raises(ValueError):
        t.add("b", [1, 42])
    assert t.get(2) is None
    assert t.add("c") == 2


def test_duplicate_dep_ids_are_kept_and_rendered_as_given():
    t = ToDoList()
    t.add("a")
    _finish(t, 1)
    assert t.add("b", [1, 1]) == 2
    assert t.render().splitlines()[1] == "2|READY_TO_EXECUTE|1,1|b"


# ------------------------------------------------------------------ set

def test_set_strictly_higher_returns_true_and_updates_status():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.IN_PROGRESS) is True
    assert t.get(1) == "1|IN_PROGRESS|a"


def test_set_same_status_returns_false():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.READY_TO_EXECUTE) is False
    assert t.set(1, S.IN_PROGRESS) is True
    assert t.set(1, S.IN_PROGRESS) is False
    assert t.get(1) == "1|IN_PROGRESS|a"


def test_set_lower_status_returns_false_and_changes_nothing():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.IN_PROGRESS) is True
    assert t.set(1, S.READY_TO_EXECUTE) is False
    assert t.set(1, S.BLOCKED) is False
    assert t.get(1) == "1|IN_PROGRESS|a"


def test_set_unknown_task_returns_false():
    t = ToDoList()
    t.add("a")
    assert t.set(9, S.IN_PROGRESS) is False
    assert t.set(9, S.FAILED) is False


def test_set_on_succeeded_task_returns_false():
    t = ToDoList()
    t.add("a")
    _finish(t, 1)
    assert t.set(1, S.FAILED) is False
    assert t.set(1, S.SUCCEEDED) is False
    assert t.get(1) == "1|SUCCEEDED|a"


def test_set_on_failed_task_returns_false():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.FAILED) is True
    assert t.set(1, S.FAILED) is False
    assert t.set(1, S.SUCCEEDED) is False
    assert t.set(1, S.IN_PROGRESS) is False
    assert t.get(1) == "1|FAILED|a"


def test_set_jump_ready_to_failed_returns_true():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.FAILED) is True
    assert t.get(1) == "1|FAILED|a"


def test_set_jump_ready_to_succeeded_returns_true():
    t = ToDoList()
    t.add("a")
    assert t.set(1, S.SUCCEEDED) is True
    assert t.get(1) == "1|SUCCEEDED|a"


def test_set_in_progress_to_succeeded_and_to_failed_both_true():
    t = ToDoList()
    t.add("a")
    t.add("b")
    assert t.set(1, S.IN_PROGRESS) is True
    assert t.set(2, S.IN_PROGRESS) is True
    assert t.set(1, S.SUCCEEDED) is True
    assert t.set(2, S.FAILED) is True
    assert t.get(1) == "1|SUCCEEDED|a"
    assert t.get(2) == "2|FAILED|b"


def test_get_after_rejected_set_is_unchanged():
    t = ToDoList()
    t.add("a")
    before = t.get(1)
    assert t.set(1, S.READY_TO_EXECUTE) is False
    assert t.set(1, S.BLOCKED) is False
    assert t.get(1) == before == "1|READY_TO_EXECUTE|a"


# ------------------------------------------------------------------ render

def test_render_empty_list_returns_empty_string():
    t = ToDoList()
    assert t.render() == ""


def test_render_uses_enum_name_not_value():
    t = ToDoList()
    t.add("a")
    t.set(1, S.IN_PROGRESS)
    assert t.render() == "1|IN_PROGRESS||a"
    assert "|2|" not in t.render()


def test_render_lists_tasks_in_id_order_joined_by_newline():
    t = ToDoList()
    t.add("first")
    t.add("second")
    t.add("third")
    assert t.render() == (
        "1|READY_TO_EXECUTE||first\n"
        "2|READY_TO_EXECUTE||second\n"
        "3|READY_TO_EXECUTE||third"
    )
    assert not t.render().endswith("\n")


def test_render_deps_field_is_comma_joined_in_given_order():
    t = ToDoList()
    t.add("a")
    t.add("b")
    _finish(t, 1)
    _finish(t, 2)
    t.add("c", [2, 1])
    assert t.render().splitlines()[2] == "3|READY_TO_EXECUTE|2,1|c"


def test_render_empty_deps_field_when_no_deps():
    t = ToDoList()
    t.add("a")
    assert t.render() == "1|READY_TO_EXECUTE||a"


def test_render_reflects_status_changes():
    t = ToDoList()
    t.add("a")
    t.add("b")
    t.set(1, S.IN_PROGRESS)
    t.set(2, S.FAILED)
    assert t.render() == "1|IN_PROGRESS||a\n2|FAILED||b"

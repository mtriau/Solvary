# Provided tests for Part 3: cursor movement, delete, cursor-aware undo/redo.

from keyboard import Keyboard


def test_spec_example():
    kb = Keyboard()
    kb.type("abc")
    assert (kb.text(), kb.cursor()) == ("abc", 3)
    kb.move_left(1)
    assert kb.cursor() == 2
    kb.type("X")
    assert (kb.text(), kb.cursor()) == ("abXc", 3)
    kb.home()
    kb.delete()
    assert (kb.text(), kb.cursor()) == ("bXc", 0)
    kb.undo()
    assert (kb.text(), kb.cursor()) == ("abXc", 0)
    kb.undo()
    assert (kb.text(), kb.cursor()) == ("abc", 2)
    kb.redo()
    assert (kb.text(), kb.cursor()) == ("abXc", 3)


def test_fresh_cursor_is_zero_and_type_moves_it():
    kb = Keyboard()
    assert kb.cursor() == 0
    kb.type("hey")
    assert kb.cursor() == 3


def test_moves_are_clamped():
    kb = Keyboard()
    kb.type("abc")
    kb.move_right(5)
    assert kb.cursor() == 3
    kb.move_left(10)
    assert kb.cursor() == 0
    kb.move_right(2)
    assert kb.cursor() == 2
    kb.end()
    assert kb.cursor() == 3
    kb.home()
    assert kb.cursor() == 0


def test_backspace_removes_before_cursor_only():
    kb = Keyboard()
    kb.type("abcdef")
    kb.move_left(2)  # cursor 4
    kb.backspace(2)
    assert (kb.text(), kb.cursor()) == ("abef", 2)
    kb.home()
    kb.backspace()  # nothing before the cursor
    assert (kb.text(), kb.cursor()) == ("abef", 0)


def test_delete_removes_after_cursor_only():
    kb = Keyboard()
    kb.type("abcdef")
    kb.home()
    kb.delete(2)
    assert (kb.text(), kb.cursor()) == ("cdef", 0)
    kb.end()
    kb.delete()  # nothing after the cursor
    assert (kb.text(), kb.cursor()) == ("cdef", 4)
    kb.move_left(1)
    kb.delete(10)
    assert (kb.text(), kb.cursor()) == ("cde", 3)


def test_insert_in_the_middle():
    kb = Keyboard()
    kb.type("ac")
    kb.move_left()
    kb.type("b")
    assert (kb.text(), kb.cursor()) == ("abc", 2)


def test_moves_are_not_actions():
    kb = Keyboard()
    kb.type("abc")
    kb.home()
    kb.end()
    kb.move_left(2)
    assert kb.undo() is True
    assert (kb.text(), kb.cursor()) == ("", 0)
    assert kb.undo() is False


def test_moves_do_not_clear_redo():
    kb = Keyboard()
    kb.type("abc")
    kb.undo()
    kb.home()
    kb.move_right(3)
    assert kb.redo() is True
    assert (kb.text(), kb.cursor()) == ("abc", 3)


def test_noop_delete_is_not_an_action():
    kb = Keyboard()
    kb.type("a")
    kb.delete()
    assert kb.undo() is True and kb.text() == ""
    assert kb.undo() is False


def test_undo_restores_cursor_of_a_middle_edit():
    kb = Keyboard()
    kb.type("hello world")
    kb.move_left(6)  # cursor 5
    kb.backspace(2)  # "hel world", cursor 3
    assert (kb.text(), kb.cursor()) == ("hel world", 3)
    kb.end()
    kb.undo()
    assert (kb.text(), kb.cursor()) == ("hello world", 5)
    kb.redo()
    assert (kb.text(), kb.cursor()) == ("hel world", 3)


def test_part_one_and_two_behaviour_still_holds():
    kb = Keyboard()
    kb.type("ab")
    kb.type("cd")
    kb.backspace()
    assert kb.text() == "abc"
    assert kb.undo() and kb.text() == "abcd"
    assert kb.undo() and kb.text() == "ab"
    assert kb.redo() and kb.text() == "abcd"

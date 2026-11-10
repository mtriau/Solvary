# Provided tests for Part 2: undo / redo.

from keyboard import Keyboard


def test_spec_example():
    kb = Keyboard()
    kb.type("ab")
    kb.type("cd")
    kb.backspace()
    assert kb.text() == "abc"
    assert kb.undo() is True and kb.text() == "abcd"
    assert kb.undo() is True and kb.text() == "ab"
    assert kb.redo() is True and kb.text() == "abcd"
    kb.type("!")
    assert kb.text() == "abcd!"
    assert kb.redo() is False
    assert kb.undo() is True and kb.undo() is True and kb.undo() is True
    assert kb.text() == ""
    assert kb.undo() is False


def test_undo_on_fresh_keyboard_is_false():
    kb = Keyboard()
    assert kb.undo() is False
    assert kb.redo() is False
    assert kb.text() == ""


def test_multi_character_type_is_one_action():
    kb = Keyboard()
    kb.type("hello")
    assert kb.undo() is True
    assert kb.text() == ""


def test_multi_character_backspace_is_one_action():
    kb = Keyboard()
    kb.type("hello")
    kb.backspace(3)
    assert kb.text() == "he"
    assert kb.undo() is True
    assert kb.text() == "hello"


def test_noops_are_not_actions():
    kb = Keyboard()
    kb.type("a")
    kb.type("")
    kb.backspace(0)
    assert kb.undo() is True and kb.text() == ""
    assert kb.undo() is False
    kb2 = Keyboard()
    kb2.backspace()
    assert kb2.undo() is False


def test_redo_after_several_undos_replays_in_order():
    kb = Keyboard()
    kb.type("1")
    kb.type("2")
    kb.type("3")
    kb.undo()
    kb.undo()
    kb.undo()
    assert kb.text() == ""
    assert kb.redo() and kb.text() == "1"
    assert kb.redo() and kb.text() == "12"
    assert kb.redo() and kb.text() == "123"
    assert kb.redo() is False


def test_new_action_clears_redo():
    kb = Keyboard()
    kb.type("a")
    kb.type("b")
    kb.undo()
    kb.type("c")
    assert kb.text() == "ac"
    assert kb.redo() is False
    assert kb.undo() and kb.text() == "a"


def test_noop_after_undo_keeps_redo():
    kb = Keyboard()
    kb.type("a")
    kb.undo()
    kb.type("")
    kb.backspace()
    assert kb.redo() is True
    assert kb.text() == "a"


def test_backspace_past_end_undo_restores_exactly():
    kb = Keyboard()
    kb.type("abc")
    kb.backspace(10)
    assert kb.text() == ""
    kb.undo()
    assert kb.text() == "abc"


def test_long_history():
    kb = Keyboard()
    for i in range(2000):
        kb.type(str(i % 10))
    for _ in range(1000):
        assert kb.undo()
    assert len(kb.text()) == 1000
    for _ in range(1000):
        assert kb.redo()
    assert len(kb.text()) == 2000

# Provided tests for Part 1: type / backspace / text.

from keyboard import Keyboard


def test_starts_empty():
    assert Keyboard().text() == ""


def test_type_appends():
    kb = Keyboard()
    kb.type("hello")
    kb.type(" world")
    assert kb.text() == "hello world"


def test_backspace_default_removes_one():
    kb = Keyboard()
    kb.type("abc")
    kb.backspace()
    assert kb.text() == "ab"


def test_backspace_n():
    kb = Keyboard()
    kb.type("hello world")
    kb.backspace(3)
    assert kb.text() == "hello wo"


def test_backspace_more_than_available_empties():
    kb = Keyboard()
    kb.type("hi")
    kb.backspace(100)
    assert kb.text() == ""


def test_backspace_on_empty_is_a_noop():
    kb = Keyboard()
    kb.backspace()
    kb.backspace(5)
    assert kb.text() == ""


def test_type_empty_string():
    kb = Keyboard()
    kb.type("")
    kb.type("x")
    kb.type("")
    assert kb.text() == "x"


def test_interleaved():
    kb = Keyboard()
    kb.type("abc")
    kb.backspace(2)
    kb.type("yz")
    kb.backspace()
    kb.type("!")
    assert kb.text() == "ay!"


def test_instances_are_independent():
    a, b = Keyboard(), Keyboard()
    a.type("a")
    b.type("b")
    assert a.text() == "a" and b.text() == "b"

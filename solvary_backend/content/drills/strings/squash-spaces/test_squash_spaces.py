from squash_spaces import squash_spaces


def test_example():
    assert squash_spaces("  hello   world ") == "hello world"


def test_tabs_and_newlines():
    assert squash_spaces("a\tb\n\nc") == "a b c"


def test_only_whitespace():
    assert squash_spaces("   ") == ""


def test_empty():
    assert squash_spaces("") == ""


def test_already_clean():
    assert squash_spaces("one two") == "one two"

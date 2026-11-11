from balanced_brackets import balanced


def test_nested_all_kinds():
    assert balanced("([]{})") is True


def test_other_characters_ignored():
    assert balanced("f(x[0]) + {y}") is True


def test_wrong_closer():
    assert balanced("(]") is False


def test_unclosed_opener():
    assert balanced("((") is False


def test_closer_with_nothing_open():
    assert balanced(")(") is False


def test_empty_is_balanced():
    assert balanced("") is True


def test_interleaved_is_not_balanced():
    assert balanced("([)]") is False

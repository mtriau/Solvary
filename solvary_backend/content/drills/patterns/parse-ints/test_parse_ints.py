from parse_ints import parse_ints


def test_example():
    assert parse_ints("1\n  2 \n\n# three\n-4\n") == [1, 2, -4]


def test_empty():
    assert parse_ints("") == []


def test_only_comments_and_blanks():
    assert parse_ints("# a\n\n   \n  # b") == []


def test_indented_comment_is_a_comment():
    assert parse_ints("   # not a number\n5") == [5]


def test_windows_newlines():
    assert parse_ints("1\r\n2\r\n") == [1, 2]


def test_values_are_ints():
    assert all(type(n) is int for n in parse_ints("1\n2"))

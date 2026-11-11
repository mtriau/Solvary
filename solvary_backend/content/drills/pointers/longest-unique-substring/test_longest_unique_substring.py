from longest_unique_substring import longest_unique


def test_example():
    assert longest_unique("abcabcbb") == 3


def test_all_same():
    assert longest_unique("bbbbb") == 1


def test_answer_in_the_middle():
    assert longest_unique("pwwkew") == 3


def test_empty():
    assert longest_unique("") == 0


def test_all_distinct():
    assert longest_unique("abcdef") == 6


def test_repeat_outside_the_window_does_not_shrink_it():
    # the second "a" is already left of the window when "b" repeats
    assert longest_unique("abba") == 2


def test_linear_time():
    s = "abcdefghij" * 20_000
    assert longest_unique(s) == 10

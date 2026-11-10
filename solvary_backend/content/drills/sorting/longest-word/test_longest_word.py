from longest_word import longest_word


def test_example():
    assert longest_word(["a", "bbb", "cc"]) == "bbb"


def test_tie_returns_first():
    assert longest_word(["aa", "bb"]) == "aa"


def test_empty_is_none():
    assert longest_word([]) is None


def test_single():
    assert longest_word(["only"]) == "only"


def test_works_on_any_iterable():
    assert longest_word(iter(["x", "yyy", "zz"])) == "yyy"

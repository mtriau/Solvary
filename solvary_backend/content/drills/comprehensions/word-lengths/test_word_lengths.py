from word_lengths import word_lengths


def test_example():
    assert word_lengths(["hi", "hello"]) == {"hi": 2, "hello": 5}


def test_empty():
    assert word_lengths([]) == {}


def test_duplicates_collapse():
    assert word_lengths(["a", "a", "bb"]) == {"a": 1, "bb": 2}


def test_empty_string_is_a_word():
    assert word_lengths([""]) == {"": 0}


def test_returns_a_plain_dict():
    assert type(word_lengths(["x"])) is dict

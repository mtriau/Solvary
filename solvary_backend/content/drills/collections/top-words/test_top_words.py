from top_words import top_words


def test_example():
    assert top_words("the cat the dog The bird", 2) == [("the", 3), ("cat", 1)]


def test_case_insensitive():
    assert top_words("A a A", 1) == [("a", 3)]


def test_empty_text():
    assert top_words("", 3) == []


def test_n_larger_than_vocabulary():
    assert top_words("x y", 10) == [("x", 1), ("y", 1)]


def test_ties_keep_first_seen_order():
    assert top_words("b a b a", 2) == [("b", 2), ("a", 2)]

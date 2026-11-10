from initials import initials


def test_example():
    assert initials(["alice", "Bob", "  carol", "anna"]) == {"A", "B", "C"}


def test_blank_names_are_skipped():
    assert initials(["", "   ", "dave"]) == {"D"}


def test_all_blank():
    assert initials(["", "   "]) == set()


def test_empty():
    assert initials([]) == set()


def test_returns_a_set():
    assert isinstance(initials(["x"]), set)

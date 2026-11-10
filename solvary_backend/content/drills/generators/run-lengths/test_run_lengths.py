from run_lengths import run_lengths


def test_example():
    assert run_lengths("aaabcc") == [("a", 3), ("b", 1), ("c", 2)]


def test_alternating():
    assert run_lengths("abab") == [("a", 1), ("b", 1), ("a", 1), ("b", 1)]


def test_empty():
    assert run_lengths("") == []


def test_single_run():
    assert run_lengths("zzzz") == [("z", 4)]


def test_counts_are_ints():
    assert all(type(n) is int for _, n in run_lengths("aab"))

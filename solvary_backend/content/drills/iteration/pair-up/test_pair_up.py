from pair_up import pair_up


def test_example():
    assert pair_up(["ann", "bob"], [90, 85]) == {"ann": 90, "bob": 85}


def test_longer_names_truncated():
    assert pair_up(["ann", "bob", "cy"], [1]) == {"ann": 1}


def test_longer_scores_truncated():
    assert pair_up(["ann"], [1, 2, 3]) == {"ann": 1}


def test_empty():
    assert pair_up([], []) == {}


def test_works_on_any_iterables():
    assert pair_up(iter(["a", "b"]), iter([1, 2])) == {"a": 1, "b": 2}

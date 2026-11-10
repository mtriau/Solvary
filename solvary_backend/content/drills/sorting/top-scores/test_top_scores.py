from top_scores import top_scores


def test_example():
    assert top_scores({"ann": 90, "bob": 95, "cy": 90, "dee": 70}, 3) == ["bob", "ann", "cy"]


def test_empty():
    assert top_scores({}, 2) == []


def test_n_larger_than_entries():
    assert top_scores({"a": 1}, 5) == ["a"]


def test_ties_by_name():
    assert top_scores({"zed": 10, "amy": 10, "kim": 10}, 2) == ["amy", "kim"]


def test_zero_n():
    assert top_scores({"a": 1}, 0) == []

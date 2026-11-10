from number_lines import number_lines


def test_example():
    assert number_lines(["alpha", "beta"]) == ["1: alpha", "2: beta"]


def test_empty():
    assert number_lines([]) == []


def test_starts_at_one():
    assert number_lines(["x"]) == ["1: x"]


def test_blank_lines_are_numbered_too():
    assert number_lines(["", "b"]) == ["1: ", "2: b"]


def test_works_on_any_iterable():
    assert number_lines(iter(["a", "b"])) == ["1: a", "2: b"]

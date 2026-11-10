from sort_versions import sort_versions


def test_example():
    assert sort_versions(["1.10.0", "1.9.0", "1.2", "1.2.1"]) == ["1.2", "1.2.1", "1.9.0", "1.10.0"]


def test_numeric_not_lexicographic():
    assert sort_versions(["10.0", "9.0", "100.0"]) == ["9.0", "10.0", "100.0"]


def test_empty():
    assert sort_versions([]) == []


def test_output_keeps_original_strings():
    assert sort_versions(["01.2", "1.1"]) == ["1.1", "01.2"]


def test_input_is_not_mutated():
    versions = ["2.0", "1.0"]
    sort_versions(versions)
    assert versions == ["2.0", "1.0"]

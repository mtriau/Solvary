from dedupe_keep_order import dedupe


def test_example():
    assert dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_string_characters():
    assert dedupe("mississippi") == ["m", "i", "s", "p"]


def test_empty():
    assert dedupe([]) == []


def test_no_duplicates_unchanged():
    assert dedupe([1, 2, 3]) == [1, 2, 3]


def test_works_on_an_iterator():
    assert dedupe(iter([2, 2, 1])) == [2, 1]


def test_linear_time_on_many_items():
    items = [i % 1000 for i in range(200_000)]
    assert dedupe(items) == list(range(1000))

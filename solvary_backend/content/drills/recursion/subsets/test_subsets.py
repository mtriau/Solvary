from subsets import subsets


def test_two_items():
    assert sorted(subsets([1, 2])) == [[], [1], [1, 2], [2]]


def test_empty_has_the_empty_subset():
    assert subsets([]) == [[]]


def test_single():
    assert sorted(subsets([7])) == [[], [7]]


def test_count_is_two_to_the_n():
    result = subsets(list(range(10)))
    assert len(result) == 1024
    assert len({tuple(s) for s in result}) == 1024


def test_subsets_keep_input_order():
    for s in subsets([3, 1, 2]):
        assert s == [x for x in [3, 1, 2] if x in s]


def test_results_are_independent_lists():
    result = subsets([1, 2, 3])
    result[0].append(99)
    assert sum(99 in s for s in result) == 1

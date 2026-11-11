from max_depth import depth


def test_empty_is_one():
    assert depth([]) == 1


def test_flat_is_one():
    assert depth([1, 2]) == 1


def test_example():
    assert depth([1, [2, [3]], [4]]) == 3


def test_depth_is_the_maximum_not_the_first():
    assert depth([[1], [[2]], 3]) == 3


def test_empty_inner_list_still_counts():
    assert depth([[]]) == 2


def test_strings_and_tuples_are_not_lists():
    assert depth(["abc", (1, (2,))]) == 1

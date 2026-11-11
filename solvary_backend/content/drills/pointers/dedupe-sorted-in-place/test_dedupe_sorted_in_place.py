from dedupe_sorted_in_place import dedupe_sorted


def test_example():
    nums = [1, 1, 2, 3, 3]
    k = dedupe_sorted(nums)
    assert k == 3
    assert nums[:k] == [1, 2, 3]


def test_no_duplicates():
    nums = [1, 2, 3]
    assert dedupe_sorted(nums) == 3
    assert nums == [1, 2, 3]


def test_all_equal():
    nums = [7, 7, 7, 7]
    k = dedupe_sorted(nums)
    assert k == 1
    assert nums[:k] == [7]


def test_empty():
    assert dedupe_sorted([]) == 0


def test_mutates_the_same_list_object():
    nums = [0, 0, 1]
    alias = nums
    k = dedupe_sorted(nums)
    assert alias is nums
    assert alias[:k] == [0, 1]
    assert len(alias) == 3  # length untouched; only the prefix matters


def test_negative_and_wide_range():
    nums = [-5, -5, -1, 0, 0, 0, 9]
    k = dedupe_sorted(nums)
    assert nums[:k] == [-5, -1, 0, 9]

from first_unique_char import first_unique


def test_example_first_position():
    assert first_unique("leetcode") == 0


def test_example_later_position():
    assert first_unique("loveleetcode") == 2


def test_all_repeat():
    assert first_unique("aabb") == -1


def test_empty():
    assert first_unique("") == -1


def test_single_character():
    assert first_unique("z") == 0


def test_linear_time():
    s = "ab" * 100_000 + "c"
    assert first_unique(s) == 200_000

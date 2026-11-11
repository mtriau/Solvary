from group_anagrams import group_anagrams


def test_example():
    words = ["eat", "tea", "tan", "ate", "nat", "bat"]
    assert group_anagrams(words) == [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]


def test_empty():
    assert group_anagrams([]) == []


def test_single_word():
    assert group_anagrams(["a"]) == [["a"]]


def test_duplicates_stay_in_the_same_group():
    assert group_anagrams(["ab", "ba", "ab"]) == [["ab", "ba", "ab"]]


def test_empty_strings_group_together():
    assert group_anagrams(["", "x", ""]) == [["", ""], ["x"]]


def test_groups_follow_first_appearance_not_size_or_alphabet():
    words = ["bat", "tan", "nat", "eat", "tea", "ate"]
    assert group_anagrams(words) == [["bat"], ["tan", "nat"], ["eat", "tea", "ate"]]
    assert group_anagrams(["zz", "ab", "ba", "z", "yy"]) == [["zz"], ["ab", "ba"], ["z"], ["yy"]]


def test_case_sensitive():
    assert group_anagrams(["Ab", "bA", "ab"]) == [["Ab", "bA"], ["ab"]]

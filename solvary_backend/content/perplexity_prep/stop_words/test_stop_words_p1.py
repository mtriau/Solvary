# Provided tests for Part 1: text_before_stop. Run with: pytest stop_words -q
# Each test name says which sentence of PROBLEM.md it checks.

from stop_words import text_before_stop


def test_spec_examples():
    assert text_before_stop("the quick brown fox jumps", ["fox", "jumps"]) == "the quick brown "
    assert text_before_stop("hello world", ["xyz"]) == "hello world"
    assert text_before_stop("stop now", ["stop"]) == ""
    assert text_before_stop("a cat sat", ["sat", "cat"]) == "a "
    assert text_before_stop("bananas", ["nan", "ana"]) == "b"


def test_returns_text_before_first_stop_word():
    assert text_before_stop("alpha beta gamma", ["gamma"]) == "alpha beta "


def test_no_stop_word_present_returns_whole_text():
    assert text_before_stop("hello world", ["xyz", "abc"]) == "hello world"


def test_stop_word_at_start_returns_empty():
    assert text_before_stop("stop now", ["stop"]) == ""


def test_earliest_occurrence_wins_regardless_of_list_order():
    assert text_before_stop("a cat sat", ["sat", "cat"]) == "a "
    assert text_before_stop("a cat sat", ["cat", "sat"]) == "a "


def test_first_of_repeated_stop_word_counts():
    assert text_before_stop("a fox b fox", ["fox"]) == "a "


def test_overlapping_candidates_earliest_wins():
    assert text_before_stop("bananas", ["nan", "ana"]) == "b"
    assert text_before_stop("bananas", ["ana", "nan"]) == "b"


def test_two_stop_words_at_the_same_position_give_the_same_prefix():
    assert text_before_stop("a cat", ["c", "cat"]) == "a "
    assert text_before_stop("a cat", ["cat", "c"]) == "a "


def test_match_is_substring_not_whole_word():
    assert text_before_stop("the catalog", ["cat"]) == "the "
    assert text_before_stop("category", ["cat"]) == ""


def test_match_is_case_sensitive():
    assert text_before_stop("Fox fox", ["fox"]) == "Fox "
    assert text_before_stop("fox", ["FOX"]) == "fox"


def test_empty_text_returns_empty():
    assert text_before_stop("", ["fox"]) == ""
    assert text_before_stop("", []) == ""


def test_empty_stop_word_list_returns_whole_text():
    assert text_before_stop("hello world", []) == "hello world"


def test_empty_string_stop_word_is_ignored():
    assert text_before_stop("abc", [""]) == "abc"
    assert text_before_stop("abc", ["", "c"]) == "ab"
    assert text_before_stop("abc", ["c", ""]) == "ab"


def test_stop_word_longer_than_text_returns_whole_text():
    assert text_before_stop("fo", ["fox"]) == "fo"
    assert text_before_stop("abc", ["abcd"]) == "abc"


def test_text_equal_to_stop_word_returns_empty():
    assert text_before_stop("fox", ["fox"]) == ""


def test_stop_word_at_the_very_end():
    assert text_before_stop("the quick fox", ["fox"]) == "the quick "


def test_stop_word_overlapping_itself():
    assert text_before_stop("aaa", ["aa"]) == ""
    assert text_before_stop("baaa", ["aa"]) == "b"


def test_does_not_mutate_the_stop_word_list():
    words = ["sat", "cat"]
    text_before_stop("a cat sat", words)
    assert words == ["sat", "cat"]

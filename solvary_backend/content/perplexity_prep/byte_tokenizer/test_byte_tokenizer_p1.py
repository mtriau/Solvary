# Byte Tokenizer, Part 1: tokenize(text, alphabet).
# Run with: pytest byte_tokenizer -q

import pytest

from byte_tokenizer import tokenize

ALPHABET = ["a", "b", "c", "ab", "abc"]


def test_spec_example_merges_ab_then_abc():
    # chars [0,1,2,0,1] -> "ab" pass [3,2,3] -> "abc" pass [4,3]
    assert tokenize("abcab", ALPHABET) == [4, 3]


def test_spec_examples_aab_and_cba():
    assert tokenize("aab", ALPHABET) == [0, 3]
    assert tokenize("cba", ALPHABET) == [2, 1, 0]


def test_empty_text_returns_empty_list():
    assert tokenize("", ALPHABET) == []


def test_text_with_no_mergeable_pairs_maps_each_char_to_its_id():
    assert tokenize("cac", ALPHABET) == [2, 0, 2]
    assert tokenize("bbb", ALPHABET) == [1, 1, 1]
    assert tokenize("ba", ALPHABET) == [1, 0]


def test_single_pass_does_not_rescan_new_token():
    # "aaa": merge (a,a) -> aa, continue AFTER it: the new "aa" is not paired
    # with the trailing "a" in the same pass.
    assert tokenize("aaa", ["a", "aa"]) == [1, 0]
    assert tokenize("aaaa", ["a", "aa"]) == [1, 1]
    assert tokenize("aaaaa", ["a", "aa"]) == [1, 1, 0]


def test_merges_apply_in_alphabet_order_not_left_to_right_position():
    # "bc" comes before "ab" in the alphabet, so "bc" merges first and "ab"
    # can never form.
    assert tokenize("abc", ["a", "b", "c", "bc", "ab"]) == [0, 3]


def test_swapping_two_tokens_in_the_alphabet_changes_the_result():
    assert tokenize("abc", ["a", "b", "c", "ab", "bc"]) == [3, 2]


def test_token_formed_in_an_earlier_pass_participates_in_later_passes():
    # "ab" pass gives [0, 2]; then "aab" = "a" + "ab" merges them.
    assert tokenize("aab", ["a", "b", "ab", "aab"]) == [3]


def test_two_multichar_tokens_merge_into_a_longer_token():
    assert tokenize("abab", ["a", "b", "ab", "abab"]) == [3]


def test_each_pass_merges_every_non_overlapping_occurrence():
    assert tokenize("abcabcabc", ALPHABET) == [4, 4, 4]
    assert tokenize("ababab", ["a", "b", "ab"]) == [2, 2, 2]


def test_multichar_token_whose_pair_never_appears_is_harmless():
    # "ba" is in the alphabet but "a"+"ab" is "aab", not "ba": nothing merges.
    assert tokenize("aab", ["a", "b", "ab", "ba"]) == [0, 2]


def test_pair_must_concatenate_to_exactly_the_token_string():
    # "abc" is formed from "ab" + "c"; the second "bc" stays "bc".
    assert tokenize("abcbc", ["a", "b", "c", "ab", "bc", "abc"]) == [5, 4]
    # "abcc" (id 4) never forms: "ab" + "c" is "abc", "abc" + "c" would need a
    # pass for "abcc" AFTER "abc", but "abcc" comes before "abc" in the alphabet.
    assert tokenize("abcc", ["a", "b", "c", "ab", "abcc", "abc"]) == [5, 2]


def test_returned_ids_concatenate_back_to_the_text():
    alphabet = ["a", "b", "c", "ab", "bc", "abc", "cab", "abcab"]
    for text in ["abcab", "cabcab", "bcbcbc", "aabbcc", "", "abcabcab"]:
        ids = tokenize(text, alphabet)
        assert all(0 <= i < len(alphabet) for i in ids), text
        assert "".join(alphabet[i] for i in ids) == text


def test_unknown_character_raises_value_error():
    with pytest.raises(ValueError):
        tokenize("abz", ALPHABET)
    with pytest.raises(ValueError):
        tokenize("z", ALPHABET)

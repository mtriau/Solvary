# Byte Tokenizer, Part 2: Tokenizer(alphabet) with tokenize / detokenize,
# built once so that per-string cost does not scale with the alphabet size.
# Run with: pytest byte_tokenizer -q

import random
import time

import pytest

from byte_tokenizer import tokenize, Tokenizer

ALPHABET = ["a", "b", "c", "ab", "abc"]


def build_big_alphabet(size: int = 50_000, seed: int = 1234) -> list[str]:
    """256 single chars, then multi-char tokens that each concatenate two
    random earlier tokens (no duplicate strings)."""
    rng = random.Random(seed)
    alphabet = [chr(i) for i in range(256)]
    seen = set(alphabet)
    while len(alphabet) < size:
        tok = rng.choice(alphabet) + rng.choice(alphabet)
        if tok not in seen:
            seen.add(tok)
            alphabet.append(tok)
    return alphabet


def random_strings(alphabet: list[str], count: int, seed: int) -> list[str]:
    """Short strings (5 to 20 chars) stitched from random alphabet entries,
    so that multi-char tokens actually occur in them."""
    rng = random.Random(seed)
    out = []
    for _ in range(count):
        target = rng.randint(5, 20)
        s = ""
        while len(s) < target:
            s += rng.choice(alphabet)
        out.append(s[:target])
    return out


# ------------------------------------------------------------ same results as Part 1

def test_class_matches_part1_function_on_spec_examples():
    t = Tokenizer(ALPHABET)
    for text in ["abcab", "aab", "cba", "", "abcabcabc", "bbbb", "cab"]:
        assert t.tokenize(text) == tokenize(text, ALPHABET), text


def test_class_single_pass_does_not_rescan_new_token():
    t = Tokenizer(["a", "aa"])
    assert t.tokenize("aaa") == [1, 0]
    assert t.tokenize("aaaaa") == [1, 1, 0]


def test_class_applies_merges_in_alphabet_order():
    assert Tokenizer(["a", "b", "c", "bc", "ab"]).tokenize("abc") == [0, 3]
    assert Tokenizer(["a", "b", "c", "ab", "bc"]).tokenize("abc") == [3, 2]


def test_class_lets_earlier_pass_tokens_participate_later():
    assert Tokenizer(["a", "b", "ab", "aab"]).tokenize("aab") == [3]
    assert Tokenizer(["a", "b", "ab", "abab"]).tokenize("abab") == [3]


def test_class_skipping_absent_merges_must_not_change_order_of_present_ones():
    # Only "ab" and "abc" occur in the text; "bc" (which sits between them in
    # the alphabet) never occurs. Skipping it must not reorder the rest.
    alphabet = ["a", "b", "c", "ab", "bc", "abc"]
    text = "abcabca"
    assert Tokenizer(alphabet).tokenize(text) == tokenize(text, alphabet) == [5, 5, 0]


def test_class_tokenize_returns_a_fresh_list_each_call():
    t = Tokenizer(ALPHABET)
    first = t.tokenize("abcab")
    first.append(-1)
    assert t.tokenize("abcab") == [4, 3]
    assert t.tokenize("abcab") is not t.tokenize("abcab")


def test_class_has_no_state_leaking_between_texts():
    t = Tokenizer(ALPHABET)
    assert t.tokenize("abcab") == [4, 3]
    assert t.tokenize("aab") == [0, 3]
    assert t.tokenize("abcab") == [4, 3]
    assert t.tokenize("") == []


def test_class_unknown_character_raises_value_error():
    t = Tokenizer(ALPHABET)
    with pytest.raises(ValueError):
        t.tokenize("abz")


# ------------------------------------------------------------ detokenize

def test_detokenize_inverts_tokenize():
    t = Tokenizer(ALPHABET)
    for text in ["abcab", "aab", "cba", "abcabcabc", "ccc"]:
        assert t.detokenize(t.tokenize(text)) == text


def test_detokenize_joins_token_strings_in_order():
    t = Tokenizer(ALPHABET)
    assert t.detokenize([4, 3]) == "abcab"
    assert t.detokenize([2, 1, 0]) == "cba"


def test_detokenize_empty_ids_returns_empty_string():
    assert Tokenizer(ALPHABET).detokenize([]) == ""


def test_detokenize_id_out_of_range_raises_value_error():
    t = Tokenizer(ALPHABET)
    with pytest.raises(ValueError):
        t.detokenize([0, 5])
    with pytest.raises(ValueError):
        t.detokenize([99])


def test_detokenize_negative_id_raises_value_error():
    # -1 is not a token id even though Python lists would accept it.
    with pytest.raises(ValueError):
        Tokenizer(ALPHABET).detokenize([-1])


# ------------------------------------------------------------ scale: 50K-entry alphabet

def test_large_alphabet_tokenizes_2000_short_strings_under_3_seconds():
    alphabet = build_big_alphabet()
    texts = random_strings(alphabet, 2000, seed=99)
    t = Tokenizer(alphabet)
    started = time.perf_counter()
    outputs = [t.tokenize(s) for s in texts]
    elapsed = time.perf_counter() - started
    assert elapsed < 3.0, f"2000 strings took {elapsed:.2f}s against a 50K alphabet"
    assert all(len(ids) <= len(s) for ids, s in zip(outputs, texts))


def test_large_alphabet_output_matches_part1_function():
    alphabet = build_big_alphabet()
    t = Tokenizer(alphabet)
    for s in random_strings(alphabet, 50, seed=7):
        assert t.tokenize(s) == tokenize(s, alphabet), repr(s)


def test_large_alphabet_detokenize_round_trips():
    alphabet = build_big_alphabet()
    t = Tokenizer(alphabet)
    for s in random_strings(alphabet, 300, seed=11):
        assert t.detokenize(t.tokenize(s)) == s

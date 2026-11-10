# Byte Tokenizer, Part 3: count_tokens and tokenize_long (chunked tokenization).
# Run with: pytest byte_tokenizer -q

import random
import time

import pytest

from byte_tokenizer import Tokenizer

ALPHABET = ["a", "b", "c", "ab", "abc"]
WS_ALPHABET = list("abcdefghij \n\t") + ["ab", "cd", "abcd", "ef", "gh", "efgh", "ij", "abcdef"]


def long_text(n_chars: int, seed: int = 5) -> str:
    rng = random.Random(seed)
    words = ["abcd", "abcdef", "efgh", "ij", "a", "ghij", "cdab", "efab", "j", "ababcd"]
    parts, n = [], 0
    while n < n_chars + 50:
        w = rng.choice(words)
        parts.append(w)
        n += len(w) + 1
    return " ".join(parts)[:n_chars]


# ------------------------------------------------------------ count_tokens

def test_count_tokens_equals_length_of_tokenize():
    t = Tokenizer(ALPHABET)
    for text in ["abcab", "aab", "cba", "abcabcabc", "bbbb", "cab"]:
        assert t.count_tokens(text) == len(t.tokenize(text)), text


def test_count_tokens_empty_text_is_zero():
    assert Tokenizer(ALPHABET).count_tokens("") == 0


def test_count_tokens_counts_merged_tokens_not_characters():
    t = Tokenizer(["a", "aa"])
    assert t.count_tokens("aaaaa") == 3


def test_count_tokens_unknown_character_raises_value_error():
    with pytest.raises(ValueError):
        Tokenizer(ALPHABET).count_tokens("abz")


# ------------------------------------------------------------ tokenize_long

def test_tokenize_long_matches_tokenize_without_whitespace():
    t = Tokenizer(WS_ALPHABET)
    for text in ["abcdefgh", "abcdabcdij", "a", "ghij", ""]:
        assert t.tokenize_long(text) == t.tokenize(text), text


def test_tokenize_long_matches_tokenize_with_whitespace():
    t = Tokenizer(WS_ALPHABET)
    for text in ["ab a ab", "abcd efgh ij", " abcd", "abcd ", "ab  cd", "a b c d"]:
        assert t.tokenize_long(text) == t.tokenize(text), repr(text)


def test_tokenize_long_keeps_whitespace_tokens_in_the_output():
    t = Tokenizer(["a", "b", " ", "ab"])
    assert t.tokenize_long("ab a ab") == [3, 2, 0, 2, 3]
    assert t.tokenize_long("  ab  ") == [2, 2, 3, 2, 2]


def test_tokenize_long_handles_newlines_and_tabs_like_spaces():
    t = Tokenizer(WS_ALPHABET)
    for text in ["abcd\nefgh\tij", "\n\nab\t", "ab\ncd\n"]:
        assert t.tokenize_long(text) == t.tokenize(text), repr(text)


def test_tokenize_long_empty_text_returns_empty_list():
    assert Tokenizer(WS_ALPHABET).tokenize_long("") == []


def test_tokenize_long_falls_back_when_a_token_contains_a_space():
    # "a a" is one token: splitting at spaces would make it impossible.
    t = Tokenizer(["a", " ", "a ", "a a"])
    assert t.tokenize_long("a a") == t.tokenize("a a") == [3]
    assert t.tokenize_long("a a a") == t.tokenize("a a a")


def test_tokenize_long_falls_back_when_a_token_spans_a_word_boundary():
    alphabet = list("abc ") + ["ab", "b c", "ab c"]
    t = Tokenizer(alphabet)
    for text in ["ab c", "ab cab c", "cab c ab", "a b c"]:
        assert t.tokenize_long(text) == t.tokenize(text), repr(text)


def test_tokenize_long_unknown_character_raises_value_error():
    with pytest.raises(ValueError):
        Tokenizer(WS_ALPHABET).tokenize_long("abcd xyz")


def test_tokenize_long_200k_chars_under_3_seconds():
    t = Tokenizer(WS_ALPHABET)
    text = long_text(200_000)
    assert len(text) == 200_000
    started = time.perf_counter()
    out = t.tokenize_long(text)
    elapsed = time.perf_counter() - started
    assert elapsed < 3.0, f"tokenize_long on 200K chars took {elapsed:.2f}s"
    assert out == t.tokenize(text)

# Provided tests for Part 2: TokenStream(stop_words, window).
# Run with: pytest stop_words -q

import time

from stop_words import TokenStream


def _stream(window: int, stop: set[str] | None = None, tokens: tuple[str, ...] = ()) -> TokenStream:
    s = TokenStream(stop or set(), window)
    for t in tokens:
        s.push(t)
    return s


def test_counts_is_empty_before_any_push():
    assert _stream(3).counts() == {}


def test_pushed_tokens_are_counted():
    s = _stream(5, tokens=("a", "b", "a"))
    assert s.counts() == {"a": 2, "b": 1}


def test_window_evicts_the_oldest_token():
    s = _stream(3, tokens=("a", "b", "a", "c"))
    assert s.counts() == {"b": 1, "a": 1, "c": 1}


def test_push_after_eviction_updates_counts():
    s = _stream(3, tokens=("a", "b", "a", "c", "a"))
    assert s.counts() == {"a": 2, "c": 1}


def test_counts_has_no_zero_entries_after_eviction():
    s = _stream(2, tokens=("a", "b", "c"))
    assert "a" not in s.counts()
    assert s.counts() == {"b": 1, "c": 1}


def test_counts_total_equals_window_size_when_full():
    s = _stream(4, tokens=tuple("abcdefg"))
    assert sum(s.counts().values()) == 4
    assert s.counts() == {"d": 1, "e": 1, "f": 1, "g": 1}


def test_window_of_one_holds_only_the_latest_token():
    s = _stream(1, tokens=("a", "b", "c"))
    assert s.counts() == {"c": 1}
    assert s.top_k(3) == ["c"]


def test_stop_word_is_ignored():
    s = _stream(3, stop={"the"}, tokens=("the", "a", "the"))
    assert s.counts() == {"a": 1}


def test_stop_word_never_evicts_anything():
    s = _stream(2, stop={"the"}, tokens=("a", "b", "the", "the", "the"))
    assert s.counts() == {"a": 1, "b": 1}


def test_stop_word_matches_whole_token_only():
    s = _stream(5, stop={"fox"}, tokens=("foxes", "fox", "afox"))
    assert s.counts() == {"foxes": 1, "afox": 1}


def test_stop_word_match_is_case_sensitive():
    s = _stream(5, stop={"the"}, tokens=("The", "the", "THE"))
    assert s.counts() == {"The": 1, "THE": 1}


def test_top_k_orders_by_count_descending():
    s = _stream(10, tokens=("b", "a", "b", "c", "c", "c"))
    assert s.top_k(3) == ["c", "b", "a"]


def test_top_k_breaks_ties_alphabetically():
    s = _stream(10, tokens=("pear", "apple", "mango"))
    assert s.top_k(3) == ["apple", "mango", "pear"]


def test_top_k_ties_are_not_insertion_order():
    s = _stream(10, tokens=("zeta", "zeta", "alpha", "alpha"))
    assert s.top_k(2) == ["alpha", "zeta"]


def test_top_k_returns_fewer_than_k_when_fewer_distinct_tokens():
    s = _stream(10, tokens=("a", "b", "a"))
    assert s.top_k(5) == ["a", "b"]


def test_top_k_truncates_to_k():
    s = _stream(10, tokens=("a", "b", "c", "d"))
    assert s.top_k(2) == ["a", "b"]


def test_top_k_zero_is_empty():
    s = _stream(10, tokens=("a", "b"))
    assert s.top_k(0) == []


def test_top_k_on_empty_window_is_empty():
    assert _stream(3).top_k(3) == []


def test_top_k_reflects_evictions():
    s = _stream(3, tokens=("a", "a", "a", "b", "b", "c"))
    assert s.counts() == {"b": 2, "c": 1}
    assert s.top_k(5) == ["b", "c"]


def test_memory_stays_bounded_by_window_after_200k_pushes():
    s = TokenStream({"stop"}, 10)
    start = time.perf_counter()
    for i in range(200_000):
        s.push("stop" if i % 7 == 0 else f"t{i % 1000}")
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"200K pushes took {elapsed:.2f}s"
    counts = s.counts()
    assert len(counts) <= 10
    assert sum(counts.values()) == 10
    assert "stop" not in counts

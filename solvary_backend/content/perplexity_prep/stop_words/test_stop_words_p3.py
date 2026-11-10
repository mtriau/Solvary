# Provided tests for Part 3: StopStream(stop_words).feed(chunk).
# Run with: pytest stop_words -q

from stop_words import StopStream


def test_feed_withholds_possible_stop_word_prefix():
    s = StopStream(["fox"])
    assert s.feed("the quick brown fo") == "the quick brown "


def test_stop_word_completing_across_chunks_emits_nothing_more():
    s = StopStream(["fox"])
    assert s.feed("the quick brown fo") == "the quick brown "
    assert s.feed("x jumps") == ""


def test_feed_after_stop_word_returns_empty_forever():
    s = StopStream(["fox"])
    s.feed("the quick brown fo")
    s.feed("x jumps")
    assert s.feed("more") == ""
    assert s.feed("fox") == ""
    assert s.feed("") == ""


def test_total_emitted_equals_text_before_stop_of_the_whole_input():
    text = "the quick brown fox jumps"
    expected = "the quick brown "
    for chunks in (
        ["the quick brown fo", "x jumps"],
        ["t", "he quick brown fox jumps"],
        list(text),
        ["the quick ", "brown ", "f", "o", "x jumps"],
        [text],
    ):
        s = StopStream(["fox", "jumps"])
        assert "".join(s.feed(c) for c in chunks) == expected, chunks


def test_stop_word_split_across_three_chunks():
    s = StopStream(["stop"])
    assert s.feed("go ") == "go "
    assert s.feed("st") == ""
    assert s.feed("o") == ""
    assert s.feed("p now") == ""
    assert s.feed("later") == ""


def test_complete_stop_word_at_the_very_start_returns_empty_and_sets_done():
    s = StopStream(["fox"])
    assert s.feed("fox") == ""
    assert s.feed(" jumps") == ""


def test_stop_word_entirely_inside_a_later_chunk():
    s = StopStream(["fox"])
    assert s.feed("abc ") == "abc "
    assert s.feed("fox") == ""
    assert s.feed("def") == ""


def test_empty_chunk_returns_empty_and_changes_nothing():
    s = StopStream(["fox"])
    assert s.feed("") == ""
    assert s.feed("ab fo") == "ab "
    assert s.feed("") == ""
    assert s.feed("g") == "fog"


def test_no_stop_word_ever_emits_everything_except_possible_prefix_tail():
    s = StopStream(["fox"])
    assert s.feed("abc") == "abc"
    assert s.feed("deg") == "deg"
    assert s.feed("f") == ""
    assert s.feed("g") == "fg"
    assert s.feed("fo") == ""
    assert s.feed("o") == "foo"


def test_withheld_prefix_is_released_once_it_cannot_complete():
    s = StopStream(["fox"])
    assert s.feed("fo") == ""
    assert s.feed("g") == "fog"


def test_withheld_tail_is_the_longest_prefix_over_all_stop_words():
    s = StopStream(["ab", "xyz"])
    assert s.feed("qqxy") == "qq"
    assert s.feed("a") == "xy"
    assert s.feed("b") == ""
    assert s.feed("zzz") == ""


def test_earliest_occurrence_in_the_buffer_wins():
    s = StopStream(["jumps", "fox"])
    assert s.feed("the fox ju") == "the "
    assert s.feed("mps") == ""


def test_stop_word_found_in_one_chunk_emits_only_up_to_it():
    s = StopStream(["fox", "jumps"])
    assert s.feed("the fox jumps over") == "the "
    assert s.feed(" more") == ""


def test_single_character_stop_word_withholds_nothing():
    s = StopStream(["x"])
    assert s.feed("abc") == "abc"
    assert s.feed("de") == "de"
    assert s.feed("x") == ""
    assert s.feed("y") == ""


def test_overlapping_candidates_across_chunks():
    s = StopStream(["nan", "ana"])
    assert s.feed("ban") == "b"
    assert s.feed("anas") == ""


def test_empty_stop_word_list_emits_everything_immediately():
    s = StopStream([])
    assert s.feed("abc") == "abc"
    assert s.feed("fox") == "fox"


def test_empty_string_stop_word_is_ignored():
    s = StopStream(["", "fox"])
    assert s.feed("abc") == "abc"
    assert s.feed("fo") == ""
    assert s.feed("x") == ""


def test_many_chunks_without_a_stop_word_emit_the_whole_input():
    s = StopStream(["fox"])
    chunks = [f"word{i} " for i in range(2_000)]
    out = "".join(s.feed(c) for c in chunks)
    assert out == "".join(chunks)

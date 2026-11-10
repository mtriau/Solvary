# Tier 2 #2: beam_search. Run with: pytest tier2/test_beam_search.py -q

import pytest

from beam_search import beam_search

EOS = "<eos>"


def seqs(result):
    return [seq for seq, _ in result]


def scores(result):
    return [score for _, score in result]


def test_spec_example():
    def step(seq):
        if len(seq) == 0:
            return [("a", -0.1), ("b", -2.0)]
        if seq[-1] == "a":
            return [(EOS, -0.5), ("b", -0.3)]
        return [(EOS, -0.1)]

    result = beam_search(step, (), beam_width=2, max_len=3, eos=EOS)
    assert seqs(result) == [("a", "b", EOS), ("a", EOS)]
    assert scores(result) == pytest.approx([-0.5, -0.6])


def test_beam_width_one_is_greedy():
    def step(seq):
        if len(seq) == 0:
            return [("a", -1.0), ("b", -0.5)]
        if seq[-1] == "a":
            return [(EOS, -0.1)]
        return [(EOS, -2.0)]

    greedy = beam_search(step, (), beam_width=1, max_len=5, eos=EOS)
    assert seqs(greedy) == [("b", EOS)]           # best first token, worse overall
    assert scores(greedy) == pytest.approx([-2.5])
    wide = beam_search(step, (), beam_width=2, max_len=5, eos=EOS)
    assert seqs(wide) == [("a", EOS), ("b", EOS)]
    assert scores(wide) == pytest.approx([-1.1, -2.5])


def test_scores_are_sums_of_logprobs_across_three_steps():
    # "b" is the worse first token but wins overall once the sums are in.
    def step(seq):
        if len(seq) == 0:
            return [("a", -0.1), ("b", -0.3)]
        if seq == ("a",):
            return [("x", -2.0)]
        if seq == ("b",):
            return [("x", -0.1)]
        return [(EOS, -0.1)]

    result = beam_search(step, (), beam_width=2, max_len=3, eos=EOS)
    assert seqs(result) == [("b", "x", EOS), ("a", "x", EOS)]
    assert scores(result) == pytest.approx([-0.5, -2.2])


def test_finished_sequence_keeps_its_slot_and_competes_by_score():
    def step(seq):
        if len(seq) == 0:
            return [("a", -0.1), ("b", -0.2), ("c", -0.3)]
        if seq == ("a",):
            return [(EOS, -0.05)]
        if seq == ("b",):
            return [("x", -0.01), ("y", -0.02)]
        return [(EOS, -0.5)]

    result = beam_search(step, (), beam_width=2, max_len=5, eos=EOS)
    # (a, eos) finished at step 2 with -0.15 and must survive the later steps.
    assert seqs(result) == [("a", EOS), ("b", "x", EOS)]
    assert scores(result) == pytest.approx([-0.15, -0.71])


def test_finished_sequence_is_dropped_when_live_ones_outscore_it():
    def step(seq):
        if len(seq) == 0:
            return [("a", -0.5), ("b", -0.1)]
        if seq == ("a",):
            return [(EOS, -0.1)]
        if seq == ("b",):
            return [("x", -0.05), ("y", -0.1)]
        return [(EOS, -0.1)]

    result = beam_search(step, (), beam_width=2, max_len=5, eos=EOS)
    assert seqs(result) == [("b", "x", EOS), ("b", "y", EOS)]
    assert scores(result) == pytest.approx([-0.25, -0.3])


def test_finished_sequences_are_never_passed_to_step_again():
    calls = []

    def step(seq):
        calls.append(seq)
        if len(seq) == 0:
            return [("a", -0.1), ("b", -0.2)]
        if seq == ("a",):
            return [(EOS, -0.1)]
        if seq == ("b",):
            return [("x", -0.1)]
        return [(EOS, -0.1)]

    beam_search(step, (), beam_width=2, max_len=6, eos=EOS)
    assert all(not seq or seq[-1] != EOS for seq in calls), calls


def test_max_len_truncation_returns_unfinished_sequences():
    def step(seq):
        return [("x", -0.1), ("y", -0.2)]       # never emits eos

    result = beam_search(step, (), beam_width=1, max_len=3, eos=EOS)
    assert seqs(result) == [("x", "x", "x")]
    assert scores(result) == pytest.approx([-0.3])


def test_max_len_counts_tokens_appended_not_total_length():
    def step(seq):
        return [("x", -0.1)]

    result = beam_search(step, ("s1", "s2"), beam_width=1, max_len=2, eos=EOS)
    assert seqs(result) == [("s1", "s2", "x", "x")]


def test_empty_step_result_finishes_that_beam_as_it_stands():
    def step(seq):
        if len(seq) == 0:
            return [("a", -0.1), ("b", -0.2)]
        if seq == ("a",):
            return []
        return [(EOS, -0.1)]

    result = beam_search(step, (), beam_width=2, max_len=5, eos=EOS)
    assert seqs(result) == [("a",), ("b", EOS)]
    assert scores(result) == pytest.approx([-0.1, -0.3])


def test_ties_break_by_lower_candidate_index():
    def step(seq):
        if len(seq) == 0:
            return [("p", -1.0), ("q", -1.0), ("r", -1.0)]
        return [(EOS, 0.0)]

    result = beam_search(step, (), beam_width=2, max_len=3, eos=EOS)
    assert seqs(result) == [("p", EOS), ("q", EOS)]
    greedy = beam_search(step, (), beam_width=1, max_len=3, eos=EOS)
    assert seqs(greedy) == [("p", EOS)]


def test_search_stops_when_every_beam_has_finished():
    calls = []

    def step(seq):
        calls.append(seq)
        return [(EOS, -0.1), (EOS, -0.2)]

    result = beam_search(step, (), beam_width=2, max_len=10, eos=EOS)
    assert len(calls) == 1
    assert seqs(result) == [(EOS,), (EOS,)]
    assert scores(result) == pytest.approx([-0.1, -0.2])


def test_result_is_sorted_by_score_descending_not_by_beam_order():
    def step(seq):
        if len(seq) == 0:
            return [("a", -0.1), ("b", -0.2)]
        if seq == ("a",):
            return [(EOS, -1.0)]
        return [(EOS, -0.1)]

    result = beam_search(step, (), beam_width=2, max_len=3, eos=EOS)
    assert seqs(result) == [("b", EOS), ("a", EOS)]
    assert scores(result) == pytest.approx([-0.3, -1.1])


def test_start_sequence_is_kept_as_the_prefix():
    def step(seq):
        if seq == ("<s>",):
            return [("a", -0.1)]
        return [(EOS, -0.1)]

    result = beam_search(step, ("<s>",), beam_width=1, max_len=4, eos=EOS)
    assert seqs(result) == [("<s>", "a", EOS)]
    assert scores(result) == pytest.approx([-0.2])


def test_returns_at_most_beam_width_sequences():
    def step(seq):
        return [("a", -0.5), ("b", -0.1), ("c", -0.3), ("d", -0.2), ("e", -0.4)]

    result = beam_search(step, (), beam_width=3, max_len=1, eos=EOS)
    assert seqs(result) == [("b",), ("d",), ("c",)]
    assert scores(result) == pytest.approx([-0.1, -0.2, -0.3])

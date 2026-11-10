# Tier 2 #4: sort_topics. Run with: pytest tier2/test_topic_sort.py -q

from topic_sort import sort_topics


def test_spec_example():
    assert sort_topics(["topic10", "topic2", "alpha", "alpha7", "beta1", "topic1"]) == [
        "alpha", "alpha7", "beta1", "topic1", "topic2", "topic10",
    ]


def test_numeric_suffix_sorts_numerically_not_lexically():
    assert sort_topics(["t10", "t9", "t100", "t1"]) == ["t1", "t9", "t10", "t100"]


def test_prefix_is_compared_before_the_number():
    assert sort_topics(["b1", "a2", "a10", "b0"]) == ["a2", "a10", "b0", "b1"]


def test_shorter_prefix_sorts_before_longer_prefix_regardless_of_number():
    assert sort_topics(["topics1", "topic99", "topic1"]) == ["topic1", "topic99", "topics1"]


def test_unnumbered_name_sorts_before_numbered_names_with_the_same_prefix():
    assert sort_topics(["x5", "x", "x1"]) == ["x", "x1", "x5"]
    assert sort_topics(["x0", "x"]) == ["x", "x0"]


def test_leading_zero_ties_keep_input_order():
    assert sort_topics(["topic02", "topic2"]) == ["topic02", "topic2"]
    assert sort_topics(["topic2", "topic02"]) == ["topic2", "topic02"]
    assert sort_topics(["topic3", "topic002", "topic1", "topic2"]) == ["topic1", "topic002", "topic2", "topic3"]


def test_all_digit_names_have_empty_prefix_and_sort_first():
    assert sort_topics(["b", "10", "2", "a"]) == ["2", "10", "a", "b"]


def test_digits_in_the_middle_belong_to_the_prefix():
    assert sort_topics(["a1b2", "a1b10", "a1b", "a1"]) == ["a1", "a1b", "a1b2", "a1b10"]


def test_large_numbers_compare_numerically():
    assert sort_topics(["n99999999999", "n100", "n5"]) == ["n5", "n100", "n99999999999"]


def test_mixed_prefixes_and_ties():
    names = ["b2", "a", "b", "a10", "a9", "b1", "c0", "b02"]
    assert sort_topics(names) == ["a", "a9", "a10", "b", "b1", "b2", "b02", "c0"]


def test_empty_list_returns_empty_list():
    assert sort_topics([]) == []


def test_input_list_is_not_mutated():
    names = ["topic2", "topic1"]
    result = sort_topics(names)
    assert result == ["topic1", "topic2"]
    assert names == ["topic2", "topic1"]

# Tier 2 #3: renumber. Run with: pytest tier2/test_citations.py -q

import random
import re

import pytest

from citations import renumber


def test_spec_example():
    text = "Cats purr [3]. Dogs bark [1]. Cats also meow [3][2]."
    sources = ["dogs.com", "birds.com", "cats.com"]
    assert renumber(text, sources) == (
        "Cats purr [1]. Dogs bark [2]. Cats also meow [1][3].",
        ["cats.com", "dogs.com", "birds.com"],
    )


def test_no_citations_returns_text_unchanged_and_empty_sources():
    assert renumber("No sources here.", ["a.com", "b.com"]) == ("No sources here.", [])
    assert renumber("", ["a.com"]) == ("", [])


def test_single_citation_becomes_one():
    assert renumber("See [2].", ["a.com", "b.com", "c.com"]) == ("See [1].", ["b.com"])


def test_same_source_cited_many_times_maps_once():
    text = "[2] and [2], then [2] again [2]."
    assert renumber(text, ["x.com", "y.com"]) == ("[1] and [1], then [1] again [1].", ["y.com"])


def test_sources_never_cited_are_dropped():
    text = "Only [4] matters."
    sources = ["a", "b", "c", "d", "e"]
    assert renumber(text, sources) == ("Only [1] matters.", ["d"])


def test_numbering_follows_first_appearance_not_source_order():
    text = "[3] then [1] then [2]"
    assert renumber(text, ["s1", "s2", "s3"]) == ("[1] then [2] then [3]", ["s3", "s1", "s2"])


def test_swapped_citations_do_not_collide():
    # [2] becomes [1]; the original [1] must then become [2], not be
    # rewritten again as if it were the new [1].
    assert renumber("[2] then [1]", ["s1", "s2"]) == ("[1] then [2]", ["s2", "s1"])


def test_rotated_citations_do_not_collide():
    assert renumber("[2][3][1]", ["s1", "s2", "s3"]) == ("[1][2][3]", ["s2", "s3", "s1"])


def test_already_ordered_citations_are_unchanged():
    text = "[1] a [2] b [3]"
    sources = ["s1", "s2", "s3"]
    assert renumber(text, sources) == (text, sources)


def test_out_of_range_citation_raises_value_error():
    with pytest.raises(ValueError):
        renumber("See [4].", ["a", "b", "c"])
    with pytest.raises(ValueError):
        renumber("See [0].", ["a", "b", "c"])
    with pytest.raises(ValueError):
        renumber("See [1].", [])


def test_numbers_outside_brackets_and_non_numeric_brackets_are_untouched():
    text = "In 2024, 3 cats [2] and [a] note [1]."
    assert renumber(text, ["s1", "s2"]) == ("In 2024, 3 cats [1] and [a] note [2].", ["s2", "s1"])


def test_multidigit_citations_are_read_as_one_number():
    sources = [f"s{i}" for i in range(1, 13)]
    assert renumber("[12] and [3] and [12]", sources) == ("[1] and [2] and [1]", ["s12", "s3"])


def test_every_renumbered_citation_points_at_the_same_source_as_before():
    rng = random.Random(3)
    sources = [f"src{i}" for i in range(1, 9)]
    for _ in range(50):
        cited = [rng.randint(1, 8) for _ in range(rng.randint(1, 12))]
        text = " ".join(f"w{i}[{n}]" if rng.random() < 0.7 else f"[{n}]" for i, n in enumerate(cited))
        new_text, new_sources = renumber(text, sources)
        new_numbers = [int(n) for n in re.findall(r"\[(\d+)\]", new_text)]
        assert len(new_numbers) == len(cited)
        assert [new_sources[n - 1] for n in new_numbers] == [sources[n - 1] for n in cited]
        assert new_sources == list(dict.fromkeys(sources[n - 1] for n in cited))
        assert sorted(set(new_numbers)) == list(range(1, len(new_sources) + 1))


def test_input_sources_list_is_not_mutated():
    sources = ["a", "b", "c"]
    renumber("[3][1]", sources)
    assert sources == ["a", "b", "c"]

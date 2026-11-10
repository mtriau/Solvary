# Provided tests for Part 1: greedy line packing under a size limit.

from markdown_chunker import split_markdown


def test_spec_examples():
    assert split_markdown("aaa\nbbb\nccc\nddd", 7) == ["aaa\nbbb", "ccc\nddd"]
    assert split_markdown("aaa\nbbb\nccc\nddd", 6) == ["aaa", "bbb", "ccc", "ddd"]
    assert split_markdown("aaa\nbbb", 100) == ["aaa\nbbb"]


def test_empty_document():
    assert split_markdown("", 10) == []


def test_single_line():
    assert split_markdown("hello", 5) == ["hello"]


def test_newline_counts_toward_size():
    # "ab\ncd" is 5 characters
    assert split_markdown("ab\ncd", 5) == ["ab\ncd"]
    assert split_markdown("ab\ncd", 4) == ["ab", "cd"]


def test_greedy_not_balanced():
    # greedy fills the first chunk as far as it can
    assert split_markdown("a\nb\nc\nd\ne", 5) == ["a\nb\nc", "d\ne"]


def test_lines_of_varying_length():
    assert split_markdown("12345\n1\n12\n123\n1234", 9) == ["12345\n1", "12\n123", "1234"]


def test_blank_lines_are_lines():
    assert split_markdown("a\n\nb", 3) == ["a\n", "b"]
    assert split_markdown("a\n\nb", 4) == ["a\n\nb"]


def test_every_chunk_fits_and_reconstructs():
    lines = [("x" * (i % 17)) for i in range(400)]
    md = "\n".join(lines)
    for max_size in (17, 25, 40, 99, 10_000):
        chunks = split_markdown(md, max_size)
        assert all(len(c) <= max_size for c in chunks)
        assert "\n".join(chunks) == md


def test_whole_document_fits():
    md = "one\ntwo\nthree"
    assert split_markdown(md, len(md)) == [md]
    assert split_markdown(md, len(md) - 1) == ["one\ntwo", "three"]

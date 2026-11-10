# Provided tests for Part 3: fenced code blocks are atomic and header-free.

from markdown_chunker import split_markdown


def test_spec_example_fence_moves_whole():
    assert split_markdown("# A\nline\n```\ncode1\ncode2\n```\ntail", 24) == [
        "# A\nline",
        "# A\n```\ncode1\ncode2\n```",
        "# A\ntail",
    ]


def test_everything_fits():
    md = "# A\n```\n# not a header\nx\n```\nafter"
    assert split_markdown(md, 100) == [md]


def test_hash_inside_fence_is_not_a_header():
    md = "# A\n```\n# B\n```\nt1\nt2\nt3"
    assert split_markdown(md, 16) == ["# A\n```\n# B\n```", "# A\nt1\nt2\nt3"]


def test_unclosed_fence_runs_to_the_end():
    assert split_markdown("# A\nx\n```\na\nb", 11) == ["# A\nx", "# A\n```\na\nb"]


def test_language_tag_opens_a_fence():
    md = "intro\n```python\n# comment\nprint(1)\n```\nnext"
    chunks = split_markdown(md, 30)
    assert chunks == ["intro", "```python\n# comment\nprint(1)\n```", "next"]


def test_two_fences_back_to_back_are_separate_units():
    md = "```\na\n```\n```\nb\n```"
    assert split_markdown(md, 9) == ["```\na\n```", "```\nb\n```"]
    assert split_markdown(md, 19) == [md]


def test_fence_never_split_even_when_lines_would_fit_individually():
    md = "h\n```\n1\n2\n3\n```"
    # the fence is 11 chars; "h" + fence = 13
    assert split_markdown(md, 12) == ["h", "```\n1\n2\n3\n```"]


def test_headers_after_a_fence_still_work():
    md = "# A\n```\n# fake\n```\n## B\nline\nmore"
    chunks = split_markdown(md, 18)
    assert chunks[0] == "# A\n```\n# fake\n```"
    assert chunks[1].startswith("# A\n## B")
    assert "# fake" not in chunks[1]

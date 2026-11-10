# Provided tests for Part 2: repeat the active headers at the top of new chunks.

from markdown_chunker import split_markdown


def test_whole_document_fits_is_unchanged():
    md = "# T\nHello\n## S\nWorld"
    assert split_markdown(md, 100) == [md]


def test_spec_example_header_chunk_repeats_only_parents():
    assert split_markdown("# A\n## B\nxxxx\n## C\nyyyy", 13) == [
        "# A\n## B\nxxxx",
        "# A\n## C\nyyyy",
    ]


def test_plain_lines_get_the_active_headers():
    assert split_markdown("# T\na\nb\n## S\nc\nd", 12) == [
        "# T\na\nb\n## S",
        "# T\n## S\nc\nd",
    ]


def test_deep_nesting_repeats_the_whole_chain():
    md = "# A\n## B\n### C\n#### D\ntext1\ntext2"
    assert split_markdown(md, 28) == [
        "# A\n## B\n### C\n#### D\ntext1",
        "# A\n## B\n### C\n#### D\ntext2",
    ]


def test_lower_level_header_clears_deeper_ones():
    md = "# A\n## B\n### C\n# D\nzz"
    assert split_markdown(md, 20) == ["# A\n## B\n### C\n# D", "# D\nzz"]


def test_same_level_header_replaces_its_sibling():
    md = "# A\n## B\nb1\n## C\nc1\nc2"
    # sizes: "# A\n## B\nb1" = 11; adding "\n## C" -> 16; "# A\n## C\nc1" = 11
    assert split_markdown(md, 14) == ["# A\n## B\nb1", "# A\n## C\nc1\nc2"]


def test_header_without_space_is_not_a_header():
    assert split_markdown("#tag\nline\n#tag2\nline2", 10) == ["#tag\nline", "#tag2", "line2"]


def test_seven_hashes_is_not_a_header():
    md = "####### x\nline\nmore"
    assert split_markdown(md, 10) == ["####### x", "line\nmore"]


def test_repeated_headers_count_toward_size():
    md = "# Head\n" + "\n".join(f"l{i}" for i in range(50))
    chunks = split_markdown(md, 20)
    assert all(len(c) <= 20 for c in chunks)
    assert all(c.startswith("# Head\n") for c in chunks)


def test_first_chunk_never_gets_a_prefix_and_body_lines_appear_once():
    sections = []
    for s in range(8):
        sections.append(f"# Section {s}")
        for p in range(3):
            sections.append(f"## Part {s}.{p}")
            sections.extend(f"line {s}.{p}.{i}" for i in range(4))
    md = "\n".join(sections)
    chunks = split_markdown(md, 60)
    assert all(len(c) <= 60 for c in chunks)
    body = [ln for c in chunks for ln in c.split("\n") if not ln.startswith("#")]
    assert body == [ln for ln in sections if not ln.startswith("#")]
    assert chunks[0].startswith("# Section 0\n## Part 0.0\n")
    # every later chunk opens with its section header then its part header
    for c in chunks[1:]:
        first, second = c.split("\n")[:2]
        assert first.startswith("# Section ")
        assert second.startswith("## Part ") or second.startswith("line ")


def test_document_with_no_headers_behaves_like_part_1():
    assert split_markdown("aaa\nbbb\nccc\nddd", 7) == ["aaa\nbbb", "ccc\nddd"]

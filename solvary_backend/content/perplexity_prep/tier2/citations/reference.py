"""Reference: citation renumbering.

One `re.sub` pass with a replacement function: the mapping old -> new is
filled in order of first appearance, so a source cited many times maps once
and renumbering can never collide (each original [n] is rewritten exactly
once, in place). Sources never cited are absent from the mapping and so are
dropped. Out-of-range citations ([0] or beyond len(sources)) raise
ValueError. O(len(text) + len(sources)).
"""

import re

_CITATION = re.compile(r"\[(\d+)\]")


def renumber(text: str, sources: list[str]) -> tuple[str, list[str]]:
    """Renumber [n] citations by first appearance; drop uncited sources. See PROBLEMS.md #3."""
    mapping: dict[int, int] = {}            # old 1-based index -> new 1-based index

    def replace(match: re.Match) -> str:
        old = int(match.group(1))
        if not 1 <= old <= len(sources):
            raise ValueError(f"citation [{old}] is out of range for {len(sources)} sources")
        if old not in mapping:
            mapping[old] = len(mapping) + 1
        return f"[{mapping[old]}]"

    new_text = _CITATION.sub(replace, text)
    return new_text, [sources[old - 1] for old in mapping]

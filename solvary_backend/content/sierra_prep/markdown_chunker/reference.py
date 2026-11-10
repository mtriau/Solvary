import re

_HEADER = re.compile(r"^(#{1,6}) ")


def _header_level(line: str) -> int:
    m = _HEADER.match(line)
    return len(m.group(1)) if m else 0


def _units(lines: list[str]) -> list[tuple[list[str], int]]:
    """(lines, header_level) per unit; a fenced block is one unit of level 0."""
    units: list[tuple[list[str], int]] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            units.append((lines[i : j + 1], 0))  # closing line included if present
            i = j + 1
        else:
            units.append(([lines[i]], _header_level(lines[i])))
            i += 1
    return units


def _size(lines: list[str]) -> int:
    return sum(len(x) for x in lines) + max(0, len(lines) - 1)


def split_markdown(markdown: str, max_size: int) -> list[str]:
    if not markdown:
        return []
    chunks: list[str] = []
    cur: list[str] = []
    stack: list[tuple[int, str]] = []  # active headers: (level, line)
    for unit, level in _units(markdown.split("\n")):
        if level:
            while stack and stack[-1][0] >= level:
                stack.pop()
            prefix = [line for _, line in stack]  # parents only
            stack.append((level, unit[0]))
        else:
            prefix = [line for _, line in stack]
        candidate = cur + unit
        if not cur or _size(candidate) <= max_size:
            cur = candidate
        else:
            chunks.append("\n".join(cur))
            cur = prefix + unit
    chunks.append("\n".join(cur))
    return chunks

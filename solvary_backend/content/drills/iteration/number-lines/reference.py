def number_lines(lines: list[str]) -> list[str]:
    return [f"{i}: {line}" for i, line in enumerate(lines, start=1)]

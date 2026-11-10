from itertools import groupby


def run_lengths(text: str) -> list[tuple[str, int]]:
    return [(char, sum(1 for _ in group)) for char, group in groupby(text)]

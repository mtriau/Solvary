"""Homepage row deduplication.

Rows are processed top to bottom, titles left to right.
* Row-local: only the first occurrence of a title in a row counts.
* Above the fold: the first `limit` KEPT titles of a row must also be new
  to the global set, and are added to it when kept.
* Below the fold: row-local checks only; the global set is untouched.
* Exempt rows skip the global set entirely (neither read nor written).
"""

from collections.abc import Iterable, Iterator


def _lookup(value, i: int, name: str):
    """Per-row value i: a plain value applies to every row, a list is indexed."""
    if not isinstance(value, list):
        return value
    if i >= len(value):
        raise ValueError(f"{name} has fewer entries than there are rows")
    return value[i]


def _walk(rows: Iterable[list[str]], n, exempt, fold_seen: set[str]) -> Iterator[list[str]]:
    """Yield deduped rows one at a time; `fold_seen` is the global set."""
    count = 0
    for i, row in enumerate(rows):
        count += 1
        limit = _lookup(n, i, "n")
        is_exempt = _lookup(exempt if exempt is not None else False, i, "exempt")
        seen_in_row: set[str] = set()
        kept: list[str] = []
        for title in row:
            if title in seen_in_row:
                continue
            seen_in_row.add(title)  # the first occurrence decides, kept or not
            if len(kept) < limit and not is_exempt:  # still above the fold
                if title in fold_seen:
                    continue
                fold_seen.add(title)
            kept.append(title)
        yield kept
    for value, name in ((n, "n"), (exempt, "exempt")):
        if isinstance(value, list) and len(value) != count:
            raise ValueError(f"{name} has more entries than there are rows")


def dedupe_stream(rows_iter: Iterable[list[str]], n, exempt=None) -> Iterator[list[str]]:
    """Lazy version: pulls one row from the source per row yielded."""
    yield from _walk(rows_iter, n, exempt, set())


def dedupe_rows(rows: list[list[str]], n, exempt: list[bool] | None = None) -> list[list[str]]:
    return list(dedupe_stream(rows, n, exempt))


def global_titles(rows: list[list[str]], n, exempt: list[bool] | None = None) -> set[str]:
    fold_seen: set[str] = set()
    for _ in _walk(rows, n, exempt, fold_seen):
        pass
    return fold_seen

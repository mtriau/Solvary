from collections.abc import Iterable


def adjacency(edges: list[tuple[str, str]], nodes: Iterable[str] = ()) -> dict[str, set[str]]:
    """Undirected adjacency sets; nodes in `nodes` appear even without edges."""
    raise NotImplementedError

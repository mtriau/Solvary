from collections import defaultdict
from collections.abc import Iterable


def adjacency(edges: list[tuple[str, str]], nodes: Iterable[str] = ()) -> dict[str, set[str]]:
    graph: defaultdict[str, set[str]] = defaultdict(set)
    for n in nodes:
        graph[n]  # noqa: B018 — touching the key creates the empty set
    for u, v in edges:
        graph[u].add(v)
        graph[v].add(u)
    return dict(graph)

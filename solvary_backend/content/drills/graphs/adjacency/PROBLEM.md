# Adjacency list from edges

Build an undirected adjacency list from a list of edges. Every endpoint appears as a key, each neighbour set contains the other endpoint, and nodes listed in `nodes` appear even if they have no edges.

### Signature

`def adjacency(edges: list[tuple[str, str]], nodes: Iterable[str] = ()) -> dict[str, set[str]]`

### Examples

```python
adjacency([("a", "b"), ("b", "c")]) == {"a": {"b"}, "b": {"a", "c"}, "c": {"b"}}
adjacency([], nodes=["x"]) == {"x": set()}
```

### Idiom

`graph = defaultdict(set)`, then for each edge `graph[u].add(v); graph[v].add(u)`. Touch isolated nodes with `graph[n]` so they exist. Return `dict(graph)` so callers get a plain dict.

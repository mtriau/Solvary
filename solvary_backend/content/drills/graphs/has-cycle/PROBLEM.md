# Detect a cycle in a directed graph

`graph` maps each node to the nodes it points to (every node appears as a key). Return whether the graph contains a directed cycle. Chains may be thousands of nodes long.

### Signature

`def has_cycle(graph: dict[str, set[str]]) -> bool`

### Examples

```python
has_cycle({"a": {"b"}, "b": {"c"}, "c": set()}) is False
has_cycle({"a": {"b"}, "b": {"a"}}) is True
has_cycle({"a": {"a"}}) is True
```

### Idiom

Either Kahn's algorithm (a cycle exists iff some node never reaches in-degree 0) or an iterative DFS with three states per node: unvisited, **on the current path**, done. Reaching a node that is on the path is a cycle; reaching a done node is not (that is just a diamond).

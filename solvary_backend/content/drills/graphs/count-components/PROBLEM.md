# Count connected components

`graph` maps each node to its neighbours in an undirected graph (every node appears as a key). Return the number of connected components. The graph may contain long chains, so recursion is not an option.

### Signature

`def count_components(graph: dict[str, set[str]]) -> int`

### Examples

```python
count_components({"a": {"b"}, "b": {"a"}, "c": set()}) == 2
count_components({}) == 0
```

### Idiom

One `seen` set shared across starts. For each unseen node, start an iterative DFS (`stack = [node]`, `while stack: n = stack.pop()`, push unseen neighbours) that marks the whole component, and count one. Marking on push keeps it linear.

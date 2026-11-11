# Topological order with Kahn's algorithm

`deps` maps each task to the set of tasks it depends on (every task appears as a key; dependencies are always keys too). Return an order in which every task comes after all of its dependencies. Raise `ValueError` if the dependencies contain a cycle.

### Signature

`def topo_order(deps: dict[str, set[str]]) -> list[str]`

### Examples

```python
topo_order({"build": {"compile"}, "compile": {"fetch"}, "fetch": set()}) == ["fetch", "compile", "build"]
topo_order({"a": {"b"}, "b": {"a"}})   # raises ValueError
```

### Idiom

Kahn's algorithm: an in-degree per task (how many dependencies are still unmet), a reverse map from a task to the tasks waiting on it, a `deque` of tasks with in-degree 0. Pop, append to the order, decrement each dependant and enqueue it when it hits 0. If the order is shorter than `deps`, there was a cycle.

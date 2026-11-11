def count_components(graph: dict[str, set[str]]) -> int:
    seen: set[str] = set()
    components = 0
    for start in graph:
        if start in seen:
            continue
        components += 1
        stack = [start]
        seen.add(start)
        while stack:
            node = stack.pop()
            for nxt in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
    return components

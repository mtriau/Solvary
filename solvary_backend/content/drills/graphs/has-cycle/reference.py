from collections import deque

WHITE, GREY, BLACK = 0, 1, 2  # unvisited, on the current path, finished


def has_cycle(graph: dict[str, set[str]]) -> bool:
    in_degree = {node: 0 for node in graph}
    for targets in graph.values():
        for t in targets:
            in_degree[t] += 1
    ready = deque(n for n, d in in_degree.items() if d == 0)
    done = 0
    while ready:
        node = ready.popleft()
        done += 1
        for t in graph[node]:
            in_degree[t] -= 1
            if in_degree[t] == 0:
                ready.append(t)
    return done != len(graph)


def has_cycle_dfs(graph: dict[str, set[str]]) -> bool:
    """Iterative three-colour DFS; the explicit stack replaces recursion."""
    colour = dict.fromkeys(graph, WHITE)
    for start in graph:
        if colour[start] != WHITE:
            continue
        stack = [(start, iter(graph[start]))]
        colour[start] = GREY
        while stack:
            node, children = stack[-1]
            for child in children:
                if colour[child] == GREY:
                    return True
                if colour[child] == WHITE:
                    colour[child] = GREY
                    stack.append((child, iter(graph[child])))
                    break
            else:
                colour[node] = BLACK
                stack.pop()
    return False

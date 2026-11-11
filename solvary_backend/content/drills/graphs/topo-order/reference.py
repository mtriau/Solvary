from collections import defaultdict, deque


def topo_order(deps: dict[str, set[str]]) -> list[str]:
    in_degree = {task: len(needs) for task, needs in deps.items()}
    dependants: defaultdict[str, list[str]] = defaultdict(list)
    for task, needs in deps.items():
        for need in needs:
            dependants[need].append(task)

    ready = deque(task for task, n in in_degree.items() if n == 0)
    order: list[str] = []
    while ready:
        task = ready.popleft()
        order.append(task)
        for waiting in dependants[task]:
            in_degree[waiting] -= 1
            if in_degree[waiting] == 0:
                ready.append(waiting)
    if len(order) != len(deps):
        raise ValueError("dependency cycle")
    return order

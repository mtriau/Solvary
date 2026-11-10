import time
from collections import deque

# ── Part 1 ─────────────────────────────────────────────────────────────


def retry(
    fn,
    *,
    attempts: int = 5,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 2.0,
    timeout: float | None = None,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    sleep=time.sleep,
    clock=time.monotonic,
):
    start = clock()
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except retry_on:
            if attempt == attempts:
                raise
            delay = min(base_delay * factor ** (attempt - 1), max_delay)
            if timeout is not None and (clock() - start) + delay > timeout:
                raise
            sleep(delay)
    raise AssertionError("unreachable")


# ── Part 2 ─────────────────────────────────────────────────────────────


def get_attribute(catalog: dict, item_id: str, key: str, default=None):
    item = catalog.get(item_id)
    if item is None:
        return default
    return item.get("attributes", {}).get(key, default)


def related_items(catalog: dict, item_id: str) -> list[str]:
    item = catalog.get(item_id)
    if item is None:
        return []
    return [r for r in item.get("related", []) if r in catalog]


def related_tree(catalog: dict, item_id: str, max_depth: int | None = None) -> dict | None:
    if item_id not in catalog:
        return None
    root = {"id": item_id, "related": []}
    # iterative DFS: (node dict, depth, path set) — path is per branch
    stack = [(root, 0, {item_id})]
    while stack:
        node, depth, path = stack.pop()
        if max_depth is not None and depth >= max_depth:
            continue
        children = []
        for child_id in related_items(catalog, node["id"]):
            if child_id in path:
                continue
            child = {"id": child_id, "related": []}
            node["related"].append(child)
            children.append(child)
        for child in reversed(children):
            stack.append((child, depth + 1, path | {child["id"]}))
    return root


# ── Part 3 ─────────────────────────────────────────────────────────────


def reachable(catalog: dict, item_id: str, max_depth: int | None = None) -> list[str]:
    if item_id not in catalog:
        return []
    seen = {item_id}
    out: list[str] = []
    queue = deque([(item_id, 0)])
    while queue:
        cur, depth = queue.popleft()
        if max_depth is not None and depth >= max_depth:
            continue
        for nxt in related_items(catalog, cur):
            if nxt in seen:
                continue
            seen.add(nxt)
            out.append(nxt)
            queue.append((nxt, depth + 1))
    return out

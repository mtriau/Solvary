def _analyse(comments: list[dict], mode: str, threshold: int | None):
    """Return (preorder ids, id -> comment, subtree sums, excluded set).

    Everything is iterative: trees can be 200k deep, far past the recursion limit.
    """
    if mode not in ("cat", "dog"):
        raise ValueError(f"unknown mode: {mode!r}")
    by_id = {c["id"]: c for c in comments}
    children: dict[int, list[int]] = {c["id"]: [] for c in comments}
    roots: list[int] = []
    for c in comments:
        parent = c["parent"]
        if parent is None:
            roots.append(c["id"])
        elif parent in children:
            children[parent].append(c["id"])
        else:
            raise ValueError(f"comment {c['id']} has unknown parent {parent}")

    # Iterative DFS from the roots over the one children map built above.
    order: list[int] = []  # parents always come before their children
    stack = roots[::-1]
    while stack:
        node = stack.pop()
        order.append(node)
        stack.extend(reversed(children[node]))

    sums = {cid: by_id[cid]["points"] for cid in order}
    for cid in reversed(order):  # post-order: children are folded into parents
        parent = by_id[cid]["parent"]
        if parent is not None:
            sums[parent] += sums[cid]

    excluded: set[int] = set()
    for cid in order:  # top-down: carry the nearest hidden comment's decision
        c = by_id[cid]
        if not c[mode]:
            qualifies = threshold is not None and sums[cid] > threshold
            if not qualifies:
                excluded.add(cid)
        elif c["parent"] in excluded:
            excluded.add(cid)
    return order, by_id, sums, excluded


def comments_to_exclude(comments: list[dict], mode: str, threshold: int | None = None) -> list[int]:
    """Ids hidden from a viewer of `mode`, in input order.

    A comment lacking the viewer flag is "hidden-category". It is excluded
    unless its subtree total strictly beats `threshold`; every other comment
    inherits the decision of its parent.
    """
    _, _, _, excluded = _analyse(comments, mode, threshold)
    return [c["id"] for c in comments if c["id"] in excluded]


def visible_comments(comments: list[dict], mode: str, threshold: int | None = None) -> list[int]:
    """The complement of comments_to_exclude, in input order."""
    _, _, _, excluded = _analyse(comments, mode, threshold)
    return [c["id"] for c in comments if c["id"] not in excluded]


def subtree_points(comments: list[dict]) -> dict[int, int]:
    """Own points plus all descendants' points, for every comment."""
    _, _, sums, _ = _analyse(comments, "cat", None)
    return {c["id"]: sums[c["id"]] for c in comments}


def render_thread(
    comments: list[dict], mode: str, threshold: int | None = None
) -> list[tuple[int, int]]:
    """Visible comments as (depth, id) in display order.

    Siblings sort by points descending, then id. A kept comment under an
    excluded ancestor hangs from its nearest visible ancestor (or is top-level).
    """
    order, by_id, _, excluded = _analyse(comments, mode, threshold)
    nearest: dict[int, int | None] = {}  # nearest visible ancestor-or-self
    kids: dict[int | None, list[int]] = {None: []}
    for cid in order:
        parent = by_id[cid]["parent"]
        above = nearest[parent] if parent is not None else None
        if cid in excluded:
            nearest[cid] = above
        else:
            nearest[cid] = cid
            kids.setdefault(above, []).append(cid)

    def ordered(ids: list[int]) -> list[int]:
        return sorted(ids, key=lambda i: (-by_id[i]["points"], i))

    result: list[tuple[int, int]] = []
    stack = [(0, cid) for cid in reversed(ordered(kids[None]))]
    while stack:
        depth, cid = stack.pop()
        result.append((depth, cid))
        stack.extend((depth + 1, k) for k in reversed(ordered(kids.get(cid, []))))
    return result

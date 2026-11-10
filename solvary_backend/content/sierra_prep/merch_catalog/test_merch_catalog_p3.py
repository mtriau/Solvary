# Provided tests for Part 3: cycles, depth limits, BFS reachability, scale.

from merch_catalog import reachable, related_tree


def rel(*ids):
    return {"name": "x", "attributes": {}, "related": list(ids)}


SPEC = {"a": rel("b", "c"), "b": rel("a", "d"), "c": rel("d"), "d": rel("a")}


def test_spec_reachable():
    assert reachable(SPEC, "a") == ["b", "c", "d"]
    assert reachable(SPEC, "a", max_depth=1) == ["b", "c"]


def test_spec_tree_with_depth_limit_and_cycle_cut():
    assert related_tree(SPEC, "a", max_depth=2) == {
        "id": "a",
        "related": [
            {"id": "b", "related": [{"id": "d", "related": []}]},
            {"id": "c", "related": [{"id": "d", "related": []}]},
        ],
    }


def test_tree_on_cycle_without_depth_limit_terminates():
    tree = related_tree(SPEC, "a")
    # a -> b -> d -> (a omitted) ; a -> c -> d -> (a omitted)
    assert tree == {
        "id": "a",
        "related": [
            {"id": "b", "related": [{"id": "d", "related": []}]},
            {"id": "c", "related": [{"id": "d", "related": []}]},
        ],
    }


def test_self_loop():
    cat = {"s": rel("s", "t"), "t": rel()}
    assert related_tree(cat, "s") == {"id": "s", "related": [{"id": "t", "related": []}]}
    assert reachable(cat, "s") == ["t"]


def test_item_repeats_across_branches_but_not_on_its_own_path():
    cat = {"r": rel("a", "b"), "a": rel("x"), "b": rel("x"), "x": rel("r")}
    assert related_tree(cat, "r") == {
        "id": "r",
        "related": [
            {"id": "a", "related": [{"id": "x", "related": []}]},
            {"id": "b", "related": [{"id": "x", "related": []}]},
        ],
    }


def test_depth_zero_is_just_the_root():
    assert related_tree(SPEC, "a", max_depth=0) == {"id": "a", "related": []}
    assert reachable(SPEC, "a", max_depth=0) == []


def test_reachable_bfs_order_by_depth_then_catalog_order():
    cat = {
        "r": rel("b", "a"),
        "a": rel("z"),
        "b": rel("y", "a"),
        "y": rel(),
        "z": rel("q"),
        "q": rel(),
    }
    assert reachable(cat, "r") == ["b", "a", "y", "z", "q"]
    assert reachable(cat, "r", max_depth=2) == ["b", "a", "y", "z"]


def test_reachable_unknown_item():
    assert reachable(SPEC, "nope") == []


def test_reachable_excludes_the_start_even_on_a_cycle():
    cat = {"a": rel("b"), "b": rel("a")}
    assert reachable(cat, "a") == ["b"]


def test_large_catalog_is_fast():
    n = 50_000
    cat = {f"i{k}": rel(f"i{(k + 1) % n}", f"i{(k * 7) % n}") for k in range(n)}
    out = reachable(cat, "i0")
    assert len(out) == n - 1
    assert out[0] == "i1"
    tree = related_tree(cat, "i0", max_depth=12)
    assert tree["id"] == "i0" and tree["related"][0]["id"] == "i1"

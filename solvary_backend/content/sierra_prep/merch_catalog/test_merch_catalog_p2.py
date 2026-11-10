# Provided tests for Part 2: attributes, direct relations, full relationship tree.

from merch_catalog import get_attribute, related_items, related_tree


def rel(*ids, name="x", **attrs):
    return {"name": name, "attributes": dict(attrs), "related": list(ids)}


SPEC = {
    "tent": rel("stakes", "lamp", "ghost", name="Tent", season=3),
    "stakes": rel(name="Stakes"),
    "lamp": rel("battery", name="Lamp", lumens=300),
    "battery": rel(name="AA"),
}


def test_get_attribute():
    assert get_attribute(SPEC, "lamp", "lumens") == 300
    assert get_attribute(SPEC, "lamp", "weight", 0) == 0
    assert get_attribute(SPEC, "lamp", "weight") is None
    assert get_attribute(SPEC, "nope", "lumens", "d") == "d"


def test_related_items_in_order_skipping_unknown():
    assert related_items(SPEC, "tent") == ["stakes", "lamp"]
    assert related_items(SPEC, "stakes") == []
    assert related_items(SPEC, "ghost") == []


def test_related_tree_spec_example():
    assert related_tree(SPEC, "tent") == {
        "id": "tent",
        "related": [
            {"id": "stakes", "related": []},
            {"id": "lamp", "related": [{"id": "battery", "related": []}]},
        ],
    }


def test_related_tree_unknown_item_is_none():
    assert related_tree(SPEC, "ghost") is None


def test_related_tree_leaf():
    assert related_tree(SPEC, "battery") == {"id": "battery", "related": []}


def test_same_item_in_two_branches_appears_twice():
    cat = {"r": rel("a", "b"), "a": rel("c"), "b": rel("c"), "c": rel()}
    assert related_tree(cat, "r") == {
        "id": "r",
        "related": [
            {"id": "a", "related": [{"id": "c", "related": []}]},
            {"id": "b", "related": [{"id": "c", "related": []}]},
        ],
    }


def test_tree_does_not_mutate_catalog():
    cat = {"r": rel("a"), "a": rel()}
    related_tree(cat, "r")
    assert cat == {"r": rel("a"), "a": rel()}


def test_deep_chain():
    cat = {f"i{k}": rel(f"i{k + 1}") for k in range(300)}
    cat["i300"] = rel()
    tree = related_tree(cat, "i0")
    depth = 0
    node = tree
    while node["related"]:
        node = node["related"][0]
        depth += 1
    assert depth == 300 and node["id"] == "i300"

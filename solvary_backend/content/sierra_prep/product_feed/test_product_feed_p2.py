# Provided tests for Part 2: resolve listings through fallback IDs.

from product_feed import resolve


def prod(pid, available, *fallbacks):
    return {"id": pid, "name": pid.upper(), "available": available, "fallback_ids": list(fallbacks)}


def catalog(*products):
    return {p["id"]: p for p in products}


def L(pid):
    return {"product_id": pid}


def test_available_product_resolves_to_itself():
    cat = catalog(prod("a", True))
    assert resolve([L("a")], cat) == [cat["a"]]


def test_returns_the_catalog_object_itself():
    cat = catalog(prod("a", True))
    assert resolve([L("a")], cat)[0] is cat["a"]


def test_first_fallback_in_order():
    cat = catalog(prod("a", False, "b", "c"), prod("b", True), prod("c", True))
    assert resolve([L("a")], cat) == [cat["b"]]


def test_skips_unavailable_fallbacks():
    cat = catalog(prod("a", False, "b", "c"), prod("b", False), prod("c", True))
    assert resolve([L("a")], cat) == [cat["c"]]


def test_depth_first_before_next_sibling():
    cat = catalog(
        prod("a", False, "b", "c"),
        prod("b", False, "d"),
        prod("c", True),
        prod("d", True, "a"),
    )
    assert resolve([L("a")], cat) == [cat["d"]]


def test_unknown_id_in_listing_is_none():
    cat = catalog(prod("a", True))
    assert resolve([L("zzz")], cat) == [None]


def test_unknown_fallback_ids_are_skipped():
    cat = catalog(prod("a", False, "ghost", "b"), prod("b", True))
    assert resolve([L("a")], cat) == [cat["b"]]


def test_nothing_available_is_none():
    cat = catalog(prod("a", False, "b"), prod("b", False))
    assert resolve([L("a")], cat) == [None]


def test_cycle_terminates_with_none():
    cat = catalog(prod("a", False, "b"), prod("b", False, "c"), prod("c", False, "a"))
    assert resolve([L("a")], cat) == [None]


def test_cycle_with_an_available_product_past_the_loop():
    cat = catalog(prod("a", False, "b"), prod("b", False, "a", "c"), prod("c", True))
    assert resolve([L("a")], cat) == [cat["c"]]


def test_self_fallback():
    cat = catalog(prod("a", False, "a"))
    assert resolve([L("a")], cat) == [None]


def test_one_result_per_listing_in_order():
    cat = catalog(prod("a", True), prod("b", False, "a"), prod("c", False))
    out = resolve([L("c"), L("b"), L("a"), L("c")], cat)
    assert out == [None, cat["a"], cat["a"], None]


def test_empty_listings():
    assert resolve([], catalog(prod("a", True))) == []


def test_long_fallback_chain():
    products = [prod(f"p{i}", False, f"p{i + 1}") for i in range(500)]
    products.append(prod("p500", True))
    cat = catalog(*products)
    assert resolve([L("p0")], cat) == [cat["p500"]]

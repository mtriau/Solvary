# Provided tests for Part 3: merge resolved products by SKU.

from product_feed import merge_listings


def P(sku, name="X", price=100, stock=1, tags=()):
    return {"sku": sku, "name": name, "price": price, "stock": stock, "tags": list(tags)}


def test_spec_example():
    out = merge_listings([
        P("S1", "Tent", 1999, 2, ["camp", "sale"]),
        None,
        P("S2", "Lamp", 500, 1, []),
        P("S1", "Tent (XL)", 1499, 3, ["xl", "camp"]),
    ])
    assert out == [
        {"sku": "S1", "name": "Tent", "price": 1499, "stock": 5, "tags": ["camp", "sale", "xl"]},
        {"sku": "S2", "name": "Lamp", "price": 500, "stock": 1, "tags": []},
    ]


def test_single_product_passes_through_as_a_new_dict():
    p = P("A", "Boot", 10, 1, ["b", "a"])
    out = merge_listings([p])
    assert out == [{"sku": "A", "name": "Boot", "price": 10, "stock": 1, "tags": ["a", "b"]}]
    assert out[0] is not p


def test_nones_are_skipped():
    assert merge_listings([None, None]) == []
    assert merge_listings([None, P("A"), None]) == [{"sku": "A", "name": "X", "price": 100, "stock": 1, "tags": []}]


def test_empty_input():
    assert merge_listings([]) == []


def test_order_is_first_appearance():
    out = merge_listings([P("B"), P("A"), P("B"), P("C"), P("A")])
    assert [o["sku"] for o in out] == ["B", "A", "C"]


def test_name_from_first_occurrence_price_min_stock_sum():
    out = merge_listings([P("A", "first", 300, 2), P("A", "second", 100, 5), P("A", "third", 200, 0)])
    assert out == [{"sku": "A", "name": "first", "price": 100, "stock": 7, "tags": []}]


def test_tags_union_sorted_unique():
    out = merge_listings([P("A", tags=["z", "m"]), P("A", tags=["m", "a"]), P("A", tags=["z"])])
    assert out[0]["tags"] == ["a", "m", "z"]


def test_input_products_are_not_mutated():
    a = P("A", "first", 300, 2, ["x"])
    b = P("A", "second", 100, 5, ["y"])
    merge_listings([a, b])
    assert a == P("A", "first", 300, 2, ["x"])
    assert b == P("A", "second", 100, 5, ["y"])


def test_output_tags_list_is_not_the_input_list():
    a = P("A", tags=["x"])
    out = merge_listings([a])
    out[0]["tags"].append("mutated")
    assert a["tags"] == ["x"]


def test_many_products_group_correctly():
    products = [P(f"S{i % 100}", price=1000 - i, stock=1, tags=[f"t{i % 3}"]) for i in range(5000)]
    out = merge_listings(products)
    assert len(out) == 100
    assert out[0]["sku"] == "S0"
    assert out[0]["stock"] == 50
    assert out[0]["price"] == 1000 - 4900
    assert out[0]["tags"] == ["t0", "t1", "t2"]

# Provided tests for Part 2: versions and checkout.

import time

import recipe_cart

RECIPES = {
    "pancakes": {"flour": 2, "egg": 2, "milk": 1},
    "omelette": {"egg": 3, "milk": 1},
    "bread": {"flour": 3, "yeast": 1},
}
DISCOUNTS = {"egg": [(8, 10), (4, 3)], "flour": [(5, 4)], "milk": [(2, 1)]}


def make():
    return recipe_cart.Cart(RECIPES, DISCOUNTS)


def test_empty_cart_is_version_zero():
    assert make().get_version() == 0


def test_each_effective_add_or_remove_creates_a_version():
    cart = make()
    cart.add_recipe("pancakes")
    assert cart.get_version() == 1
    cart.add_recipe("pancakes")
    assert cart.get_version() == 2
    cart.remove_recipe("pancakes")
    assert cart.get_version() == 3


def test_failed_operations_do_not_create_versions():
    cart = make()
    assert cart.add_recipe("pizza") is False
    assert cart.remove_recipe("bread") is False
    assert cart.get_version() == 0
    cart.add_recipe("bread")
    assert cart.remove_recipe("pancakes") is False
    assert cart.get_version() == 1


def test_reads_never_create_versions():
    cart = make()
    cart.add_recipe("pancakes")
    for _ in range(3):
        cart.get_total_discount()
        cart.ingredient_counts()
        cart.get_version()
    assert cart.get_version() == 1


def test_checkout_restores_counts_and_discount():
    cart = make()
    cart.add_recipe("pancakes")
    cart.add_recipe("pancakes")
    cart.add_recipe("bread")
    assert cart.checkout(2) is True
    assert cart.ingredient_counts() == {"flour": 4, "egg": 4, "milk": 2}
    assert cart.get_total_discount() == 4
    assert cart.get_version() == 2


def test_checkout_restores_state_across_removals():
    cart = make()
    cart.add_recipe("pancakes")      # v1
    cart.add_recipe("bread")         # v2
    cart.remove_recipe("pancakes")   # v3
    assert cart.ingredient_counts() == {"flour": 3, "yeast": 1}
    cart.checkout(2)
    assert cart.ingredient_counts() == {"flour": 5, "egg": 2, "milk": 1, "yeast": 1}
    cart.checkout(1)
    assert cart.ingredient_counts() == {"flour": 2, "egg": 2, "milk": 1}


def test_checkout_discards_newer_versions():
    cart = make()
    cart.add_recipe("pancakes")      # v1
    cart.add_recipe("bread")         # v2
    cart.add_recipe("omelette")      # v3
    assert cart.checkout(1) is True
    assert cart.checkout(2) is False  # gone for good
    assert cart.checkout(3) is False
    assert cart.get_version() == 1
    assert cart.ingredient_counts() == {"flour": 2, "egg": 2, "milk": 1}


def test_next_mutation_after_checkout_renumbers_from_restored_version():
    cart = make()
    cart.add_recipe("pancakes")      # v1
    cart.add_recipe("bread")         # v2
    cart.checkout(1)
    assert cart.add_recipe("omelette") is True
    assert cart.get_version() == 2   # a new v2, not v3
    assert cart.ingredient_counts() == {"flour": 2, "egg": 5, "milk": 2}
    cart.add_recipe("omelette")
    cart.add_recipe("omelette")
    assert cart.get_version() == 4
    assert cart.checkout(2) is True
    assert cart.ingredient_counts() == {"flour": 2, "egg": 5, "milk": 2}
    assert cart.checkout(1) is True
    assert cart.ingredient_counts() == {"flour": 2, "egg": 2, "milk": 1}


def test_checkout_of_nonexistent_version_is_false_and_changes_nothing():
    cart = make()
    cart.add_recipe("pancakes")
    assert cart.checkout(2) is False
    assert cart.checkout(-1) is False
    assert cart.get_version() == 1
    assert cart.ingredient_counts() == {"flour": 2, "egg": 2, "milk": 1}


def test_checkout_of_current_version_is_a_true_noop():
    cart = make()
    assert cart.checkout(0) is True
    cart.add_recipe("bread")
    assert cart.checkout(1) is True
    assert cart.get_version() == 1
    assert cart.ingredient_counts() == {"flour": 3, "yeast": 1}


def test_worked_example_1_3_1_0():
    recipes = {"A": {"egg": 2}, "B": {"egg": 2, "milk": 1}}
    cart = recipe_cart.Cart(recipes, {"egg": [(4, 3)]})
    out = []
    cart.add_recipe("A")
    out.append(cart.get_version())
    cart.add_recipe("B")
    out.append(cart.get_total_discount())
    cart.checkout(1)
    out.append(cart.get_version())
    out.append(cart.get_total_discount())
    assert out == [1, 3, 1, 0]


def test_long_history_stays_fast_and_checkouts_are_correct():
    # 200 recipes x 50 private ingredients: the cart ends up with 10,000
    # distinct ingredients. A full snapshot per version would copy that
    # growing dict 20,000 times; compact operations do not.
    recipes = {
        f"r{r}": {f"i{r}_{k}": 1 + k % 3 for k in range(50)} for r in range(200)
    }
    discounts = {f"i{r}_0": [(10, 1)] for r in range(200)}
    cart = recipe_cart.Cart(recipes, discounts)
    start = time.perf_counter()
    for n in range(20_000):
        assert cart.add_recipe(f"r{n % 200}") is True
    assert cart.get_version() == 20_000
    assert cart.get_total_discount() == 200          # each i{r}_0 reached 100
    assert cart.checkout(10_000) is True
    assert cart.get_version() == 10_000
    assert cart.get_total_discount() == 200          # 50 copies each
    assert cart.checkout(5) is True
    assert cart.ingredient_counts() == {
        f"i{r}_{k}": 1 + k % 3 for r in range(5) for k in range(50)
    }
    assert cart.checkout(10_000) is False
    cart.add_recipe("r7")
    assert cart.get_version() == 6
    assert time.perf_counter() - start < 2.0

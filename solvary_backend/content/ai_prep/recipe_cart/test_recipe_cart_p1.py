# Provided tests for Part 1: recipes and bulk discounts.

import recipe_cart

RECIPES = {
    "pancakes": {"flour": 2, "egg": 2, "milk": 1},
    "omelette": {"egg": 3, "milk": 1},
    "bread": {"flour": 3, "yeast": 1},
    "salad": {"lettuce": 1},
}
# Tiers are deliberately not sorted.
DISCOUNTS = {
    "egg": [(8, 10), (4, 3)],
    "flour": [(5, 4)],
    "milk": [(2, 1)],
}


def make():
    return recipe_cart.Cart(RECIPES, DISCOUNTS)


def test_unknown_recipe_cannot_be_added():
    cart = make()
    assert cart.add_recipe("pizza") is False
    assert cart.ingredient_counts() == {}
    assert cart.get_total_discount() == 0


def test_add_known_recipe_returns_true_and_counts_ingredients():
    cart = make()
    assert cart.add_recipe("pancakes") is True
    assert cart.ingredient_counts() == {"flour": 2, "egg": 2, "milk": 1}


def test_same_recipe_twice_doubles_ingredients():
    cart = make()
    assert cart.add_recipe("pancakes") is True
    assert cart.add_recipe("pancakes") is True
    assert cart.ingredient_counts() == {"flour": 4, "egg": 4, "milk": 2}


def test_counts_combine_across_recipes():
    cart = make()
    cart.add_recipe("pancakes")
    cart.add_recipe("omelette")
    assert cart.ingredient_counts() == {"flour": 2, "egg": 5, "milk": 2}


def test_remove_takes_off_exactly_one_copy():
    cart = make()
    cart.add_recipe("pancakes")
    cart.add_recipe("pancakes")
    assert cart.remove_recipe("pancakes") is True
    assert cart.ingredient_counts() == {"flour": 2, "egg": 2, "milk": 1}
    assert cart.remove_recipe("pancakes") is True
    assert cart.ingredient_counts() == {}


def test_remove_recipe_not_in_cart_is_false_and_changes_nothing():
    cart = make()
    assert cart.remove_recipe("pancakes") is False   # known, never added
    assert cart.remove_recipe("pizza") is False      # unknown
    cart.add_recipe("bread")
    assert cart.remove_recipe("pancakes") is False
    assert cart.ingredient_counts() == {"flour": 3, "yeast": 1}
    cart.remove_recipe("bread")
    assert cart.remove_recipe("bread") is False      # already gone


def test_ingredients_at_zero_are_not_listed():
    cart = make()
    cart.add_recipe("pancakes")
    cart.add_recipe("salad")
    cart.remove_recipe("pancakes")
    assert cart.ingredient_counts() == {"lettuce": 1}


def test_no_discount_below_every_threshold():
    cart = make()
    cart.add_recipe("pancakes")      # egg 2, flour 2, milk 1: nothing reached
    assert cart.get_total_discount() == 0
    assert make().get_total_discount() == 0


def test_discount_sums_each_ingredient_once():
    cart = make()
    cart.add_recipe("pancakes")
    cart.add_recipe("pancakes")      # egg 4 -> 3, flour 4 -> none, milk 2 -> 1
    assert cart.get_total_discount() == 4
    cart.add_recipe("bread")         # flour 7 -> 4 (counted once, not per 5)
    assert cart.get_total_discount() == 8


def test_only_the_highest_qualifying_tier_counts():
    cart = make()
    for _ in range(4):
        cart.add_recipe("pancakes")  # egg 8: tier (8,10) only, not 10 + 3
    # egg 8 -> 10, flour 8 -> 4, milk 4 -> 1
    assert cart.get_total_discount() == 15
    cart.remove_recipe("pancakes")   # egg 6 falls back to tier (4,3)
    assert cart.get_total_discount() == 3 + 4 + 1


def test_tier_is_chosen_by_threshold_not_by_amount():
    discounts = {"egg": [(2, 9), (6, 5), (4, 7)], "flour": []}
    cart = recipe_cart.Cart({"e": {"egg": 1}, "f": {"flour": 9}}, discounts)
    for _ in range(3):
        cart.add_recipe("e")
    assert cart.get_total_discount() == 9       # egg 3: only (2, 9)
    cart.add_recipe("e")
    assert cart.get_total_discount() == 7       # egg 4: (4, 7), though 9 is larger
    cart.add_recipe("e")
    cart.add_recipe("e")
    assert cart.get_total_discount() == 5       # egg 6: (6, 5)
    cart.add_recipe("f")                        # empty tier list
    assert cart.get_total_discount() == 5


def test_ingredient_without_discount_entry_is_free_of_discount():
    cart = make()
    for _ in range(10):
        cart.add_recipe("salad")     # lettuce has no tiers
    assert cart.get_total_discount() == 0

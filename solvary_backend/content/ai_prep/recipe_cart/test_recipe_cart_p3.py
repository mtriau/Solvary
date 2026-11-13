# Provided tests for Part 3: nested transactions.

import recipe_cart

RECIPES = {
    "pancakes": {"flour": 2, "egg": 2, "milk": 1},
    "omelette": {"egg": 3, "milk": 1},
    "bread": {"flour": 3, "yeast": 1},
}
DISCOUNTS = {"egg": [(8, 10), (4, 3)], "flour": [(5, 4)], "milk": [(2, 1)]}

PANCAKES = {"flour": 2, "egg": 2, "milk": 1}


def make():
    return recipe_cart.Cart(RECIPES, DISCOUNTS)


def test_commit_and_abort_without_open_scope_return_false_and_do_nothing():
    cart = make()
    cart.add_recipe("pancakes")
    assert cart.commit() is False
    assert cart.abort() is False
    assert cart.ingredient_counts() == PANCAKES
    assert cart.get_version() == 1
    assert cart.begin() is True
    assert cart.commit() is True
    assert cart.commit() is False       # the scope is already closed
    assert cart.abort() is False


def test_queries_see_uncommitted_changes():
    cart = make()
    cart.begin()
    cart.add_recipe("pancakes")
    cart.add_recipe("pancakes")
    assert cart.ingredient_counts() == {"flour": 4, "egg": 4, "milk": 2}
    assert cart.get_total_discount() == 4
    cart.remove_recipe("pancakes")
    assert cart.ingredient_counts() == PANCAKES


def test_abort_reverses_everything_in_the_scope():
    cart = make()
    cart.add_recipe("bread")
    cart.begin()
    cart.add_recipe("pancakes")
    cart.remove_recipe("bread")
    cart.add_recipe("omelette")
    assert cart.abort() is True
    assert cart.ingredient_counts() == {"flour": 3, "yeast": 1}
    assert cart.get_total_discount() == 0


def test_outer_abort_reverses_inner_committed_scope():
    cart = make()
    cart.begin()
    cart.add_recipe("pancakes")
    cart.begin()
    cart.add_recipe("bread")
    assert cart.commit() is True        # inner commit is only provisional
    assert cart.ingredient_counts() == {
        "flour": 5, "egg": 2, "milk": 1, "yeast": 1,
    }
    assert cart.abort() is True
    assert cart.ingredient_counts() == {}


def test_inner_abort_keeps_the_outer_scopes_earlier_changes():
    cart = make()
    cart.begin()
    cart.add_recipe("pancakes")
    cart.begin()
    cart.add_recipe("bread")
    cart.remove_recipe("pancakes")
    assert cart.abort() is True
    assert cart.ingredient_counts() == PANCAKES
    assert cart.commit() is True
    assert cart.ingredient_counts() == PANCAKES


def test_three_levels_mixed_outcomes():
    cart = make()
    cart.begin()                        # level 1
    cart.add_recipe("pancakes")
    cart.begin()                        # level 2
    cart.add_recipe("omelette")
    cart.begin()                        # level 3
    cart.add_recipe("bread")
    cart.abort()                        # drops bread only
    assert cart.ingredient_counts() == {"flour": 2, "egg": 5, "milk": 2}
    cart.commit()                       # omelette joins level 1
    cart.begin()
    cart.remove_recipe("pancakes")
    cart.commit()
    assert cart.ingredient_counts() == {"egg": 3, "milk": 1}
    cart.abort()                        # level 1: everything goes
    assert cart.ingredient_counts() == {}


def test_nesting_works_to_depth_100_and_unwinds():
    cart = make()
    for _ in range(100):
        assert cart.begin() is True
        cart.add_recipe("bread")
    assert cart.ingredient_counts() == {"flour": 300, "yeast": 100}
    for _ in range(100):
        assert cart.abort() is True
    assert cart.ingredient_counts() == {}
    assert cart.abort() is False


def test_begin_beyond_depth_100_is_refused():
    cart = make()
    for _ in range(100):
        assert cart.begin() is True
    assert cart.begin() is False
    cart.add_recipe("bread")
    assert cart.abort() is True         # closes level 100, not a phantom 101st
    assert cart.ingredient_counts() == {}
    assert cart.begin() is True         # a slot is free again


def test_mutations_inside_a_scope_create_no_versions():
    cart = make()
    cart.add_recipe("bread")            # v1
    cart.begin()
    cart.add_recipe("pancakes")
    cart.begin()
    cart.add_recipe("omelette")
    cart.commit()
    assert cart.get_version() == 1      # nothing yet, even after an inner commit
    cart.commit()
    assert cart.get_version() == 2      # the whole transaction is ONE version


def test_top_level_commit_with_no_effective_change_creates_no_version():
    cart = make()
    cart.begin()
    cart.commit()
    assert cart.get_version() == 0
    cart.begin()
    cart.add_recipe("pizza")            # fails
    cart.commit()
    assert cart.get_version() == 0


def test_checkout_while_a_transaction_is_open_is_refused():
    cart = make()
    cart.add_recipe("bread")            # v1
    cart.add_recipe("pancakes")         # v2
    cart.begin()
    cart.add_recipe("omelette")
    assert cart.checkout(1) is False
    assert cart.ingredient_counts() == {
        "flour": 5, "yeast": 1, "egg": 5, "milk": 2,
    }
    cart.abort()
    assert cart.get_version() == 2      # an abort creates no version
    assert cart.checkout(1) is True
    assert cart.ingredient_counts() == {"flour": 3, "yeast": 1}


def test_committed_transaction_is_restored_and_discarded_as_one_version():
    cart = make()
    cart.add_recipe("bread")            # v1
    cart.begin()
    cart.add_recipe("pancakes")
    cart.add_recipe("omelette")
    cart.commit()                       # v2
    cart.add_recipe("bread")            # v3
    assert cart.get_version() == 3
    cart.checkout(1)
    assert cart.ingredient_counts() == {"flour": 3, "yeast": 1}
    cart.checkout(0)
    assert cart.ingredient_counts() == {}
    cart.add_recipe("pancakes")
    cart.begin()
    cart.add_recipe("pancakes")
    cart.commit()
    assert cart.get_version() == 2
    assert cart.checkout(1) is True
    assert cart.ingredient_counts() == PANCAKES
    assert cart.checkout(2) is False

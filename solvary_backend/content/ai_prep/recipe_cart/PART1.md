# Recipe Shopping Cart: Part 1

You are building the shopping cart of a cooking app. Users add recipes to
the cart; each recipe lists ingredients, and when an ingredient appears in
several recipes the combined quantity can unlock a bulk discount. This is
Decagon's phone-screen problem: roughly 45 minutes, usually followed by a
second short problem. The interviewer cares about a space-efficient history
design in the later parts and about you stating time and space costs as you
go.

### What to implement

Module `recipe_cart`, class `Cart`:

- `Cart(recipes, discounts)`:
  - `recipes: dict[str, dict[str, int]]` maps a recipe name to
    `{ingredient: quantity}` (quantities are positive integers).
  - `discounts: dict[str, list[tuple[int, int]]]` maps an ingredient to a
    list of `(threshold, amount)` tiers.
- `add_recipe(name: str) -> bool`: put one copy of the recipe in the cart.
  Returns `True`, or `False` if the recipe is not in the recipe book.
- `remove_recipe(name: str) -> bool`: take one copy of the recipe out.
  Returns `True`, or `False` if no copy is in the cart.
- `ingredient_counts() -> dict[str, int]`: total quantity of each
  ingredient across everything in the cart.
- `get_total_discount() -> int`: the discount for the current cart.

### Rules

1. The same recipe may be added any number of times; each copy contributes
   its ingredients again.
2. `remove_recipe` removes exactly one copy.
3. `ingredient_counts()` lists only ingredients with a count above zero.
4. For each ingredient, look at its tiers whose `threshold <= count`. The
   tier with the **highest threshold** among them contributes its `amount`
   **once**; the other tiers do not stack. The total discount is the sum of
   these over all ingredients in the cart.
5. Tiers may come in any order. Within one ingredient the thresholds are
   distinct. The tier is chosen by its threshold, not by which amount is
   largest.
6. An ingredient with no tiers (empty list or no entry) contributes `0`; so
   does one whose count is below every threshold. An empty cart has
   discount `0`.

### Worked example

```python
recipes = {"A": {"egg": 2}, "B": {"egg": 2, "milk": 1}}
cart = Cart(recipes, {"egg": [(4, 3)]})
cart.add_recipe("A")          # -> True
cart.add_recipe("Z")          # -> False
cart.get_total_discount()     # -> 0   (egg 2 < 4)
cart.add_recipe("A")          # -> True (duplicates are allowed)
cart.ingredient_counts()      # -> {"egg": 4}
cart.get_total_discount()     # -> 3
cart.remove_recipe("A")       # -> True (one copy)
cart.remove_recipe("B")       # -> False
```

### Clarifications

- **Can the same recipe be added twice?** Yes, and its ingredients count
  twice.
- **What does `remove_recipe` do for a recipe that is in the cart twice?**
  Removes one copy; one stays.
- **Unknown recipe name in `remove_recipe`?** `False`.
- **Does a bigger count stack several tiers?** No. Only the highest
  qualifying tier counts, once.
- **Does a tier with a larger amount but lower threshold win?** No; the
  highest qualifying threshold wins, whatever its amount.
- **Ingredients that reach zero after removals?** Not listed in
  `ingredient_counts()`.
- **Any performance constraints?** Not in this part.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

Graders look at the data model (a count of copies per recipe plus running
ingredient totals, rather than recomputing from a list every time) and at
the discount rule: highest qualifying threshold only, once per ingredient,
tiers not assumed sorted. They also watch whether you volunteer time
complexity for each method. Part 2 will ask for versions, so a clean
add/remove pair is worth having now.

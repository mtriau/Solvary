class Cart:
    """Part 1: recipes and bulk discounts. See the statement."""

    def __init__(
        self,
        recipes: dict[str, dict[str, int]],
        discounts: dict[str, list[tuple[int, int]]],
    ) -> None:
        raise NotImplementedError

    def add_recipe(self, name: str) -> bool:
        raise NotImplementedError

    def remove_recipe(self, name: str) -> bool:
        raise NotImplementedError

    def ingredient_counts(self) -> dict[str, int]:
        raise NotImplementedError

    def get_total_discount(self) -> int:
        raise NotImplementedError

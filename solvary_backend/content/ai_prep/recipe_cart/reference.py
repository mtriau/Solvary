MAX_DEPTH = 100


class Cart:
    def __init__(self, recipes, discounts):
        self._recipes = {name: dict(ings) for name, ings in recipes.items()}
        # Tiers sorted by threshold, highest first, so the first match wins.
        self._tiers = {
            ing: sorted(tiers, reverse=True) for ing, tiers in discounts.items()
        }
        self._in_cart: dict[str, int] = {}   # recipe name -> copies
        self._counts: dict[str, int] = {}    # ingredient -> total quantity
        # History: one entry per version, each a short list of ("add"|"remove", name)
        # operations. Version n is the state after applying history[:n].
        self._history: list[list[tuple[str, str]]] = []
        # Open transactions: each frame is the list of ops applied inside it.
        self._frames: list[list[tuple[str, str]]] = []

    # ── low-level mutation (no history, no validation of the result) ──

    def _apply(self, op: str, name: str) -> bool:
        sign = 1 if op == "add" else -1
        if name not in self._recipes:
            return False
        if sign < 0 and self._in_cart.get(name, 0) == 0:
            return False
        self._shift(name, sign)
        return True

    def _shift(self, name: str, sign: int) -> None:
        copies = self._in_cart.get(name, 0) + sign
        if copies:
            self._in_cart[name] = copies
        else:
            del self._in_cart[name]
        for ing, qty in self._recipes[name].items():
            total = self._counts.get(ing, 0) + sign * qty
            if total:
                self._counts[ing] = total
            else:
                del self._counts[ing]

    @staticmethod
    def _inverse(op: tuple[str, str]) -> tuple[str, str]:
        kind, name = op
        return ("remove" if kind == "add" else "add", name)

    def _undo_ops(self, ops: list[tuple[str, str]]) -> None:
        for op in reversed(ops):
            self._apply(*self._inverse(op))

    # ── Part 1 + 2 ─────────────────────────────────────────────────

    def _mutate(self, op: str, name: str) -> bool:
        if not self._apply(op, name):
            return False
        if self._frames:
            self._frames[-1].append((op, name))
        else:
            self._history.append([(op, name)])
        return True

    def add_recipe(self, name):
        return self._mutate("add", name)

    def remove_recipe(self, name):
        return self._mutate("remove", name)

    def ingredient_counts(self):
        return dict(self._counts)

    def get_total_discount(self):
        total = 0
        for ing, count in self._counts.items():
            for threshold, amount in self._tiers.get(ing, ()):
                if threshold <= count:
                    total += amount
                    break
        return total

    def get_version(self):
        return len(self._history)

    def checkout(self, version):
        if self._frames or not 0 <= version <= len(self._history):
            return False
        while len(self._history) > version:
            self._undo_ops(self._history.pop())
        return True

    # ── Part 3 ─────────────────────────────────────────────────────

    def begin(self):
        if len(self._frames) >= MAX_DEPTH:
            return False
        self._frames.append([])
        return True

    def commit(self):
        if not self._frames:
            return False
        ops = self._frames.pop()
        if self._frames:
            self._frames[-1].extend(ops)   # outer scope can still abort these
        elif ops:
            self._history.append(ops)      # top level: one new version
        return True

    def abort(self):
        if not self._frames:
            return False
        self._undo_ops(self._frames.pop())
        return True

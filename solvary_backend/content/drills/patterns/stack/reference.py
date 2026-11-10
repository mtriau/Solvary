class Stack:
    def __init__(self) -> None:
        self._items: list = []

    def push(self, item) -> None:
        self._items.append(item)

    def pop(self):
        return self._items.pop()

    def peek(self):
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        return reversed(self._items)

    def __repr__(self) -> str:
        return f"Stack({list(self)!r})"

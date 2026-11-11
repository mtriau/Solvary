def subsets(items: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    chosen: list[int] = []

    def go(start: int) -> None:
        out.append(chosen.copy())
        for i in range(start, len(items)):
            chosen.append(items[i])
            go(i + 1)
            chosen.pop()

    go(0)
    return out

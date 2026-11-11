def generate_parens(n: int) -> list[str]:
    out: list[str] = []

    def go(partial: str, opened: int, closed: int) -> None:
        if len(partial) == 2 * n:
            out.append(partial)
            return
        if opened < n:
            go(partial + "(", opened + 1, closed)
        if closed < opened:
            go(partial + ")", opened, closed + 1)

    go("", 0, 0)
    return out

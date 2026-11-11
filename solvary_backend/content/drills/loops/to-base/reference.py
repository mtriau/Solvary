def to_base(n: int, base: int) -> list[int]:
    digits: list[int] = []
    while n:
        n, d = divmod(n, base)
        digits.append(d)
    return digits[::-1] or [0]

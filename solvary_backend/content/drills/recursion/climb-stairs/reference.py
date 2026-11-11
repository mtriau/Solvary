from functools import cache


@cache
def climb(n: int) -> int:
    if n < 2:
        return 1
    return climb(n - 1) + climb(n - 2)


def climb_iterative(n: int) -> int:
    a, b = 1, 1  # ways(0), ways(1)
    for _ in range(n):
        a, b = b, a + b
    return a

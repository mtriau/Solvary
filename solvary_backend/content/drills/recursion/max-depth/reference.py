def depth(nested: list) -> int:
    return 1 + max((depth(x) for x in nested if isinstance(x, list)), default=0)

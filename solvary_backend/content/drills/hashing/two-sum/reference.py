def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    seen: dict[int, int] = {}
    for j, x in enumerate(nums):
        if (i := seen.get(target - x)) is not None:
            return i, j
        seen.setdefault(x, j)
    return None

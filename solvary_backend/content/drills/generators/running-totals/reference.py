from itertools import accumulate


def running_totals(nums: list[int]) -> list[int]:
    return list(accumulate(nums))

import math


def min_window_sum(nums: list[int], k: int) -> int:
    best = math.inf
    total = left = 0
    for right, x in enumerate(nums):
        total += x
        while total >= k:
            best = min(best, right - left + 1)
            total -= nums[left]
            left += 1
    return 0 if best is math.inf else best

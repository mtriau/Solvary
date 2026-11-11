from collections import Counter


def count_subarrays(nums: list[int], k: int) -> int:
    seen = Counter({0: 1})
    prefix = total = 0
    for x in nums:
        prefix += x
        total += seen[prefix - k]
        seen[prefix] += 1
    return total

def pair_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        total = nums[lo] + nums[hi]
        if total == target:
            return nums[lo], nums[hi]
        if total < target:
            lo += 1
        else:
            hi -= 1
    return None

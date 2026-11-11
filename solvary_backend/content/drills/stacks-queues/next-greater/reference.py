def next_greater(nums: list[int]) -> list[int]:
    result = [-1] * len(nums)
    waiting: list[int] = []  # indices with no greater element seen yet
    for i, x in enumerate(nums):
        while waiting and nums[waiting[-1]] < x:
            result[waiting.pop()] = x
        waiting.append(i)
    return result

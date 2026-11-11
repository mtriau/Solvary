def dedupe_sorted(nums: list[int]) -> int:
    if not nums:
        return 0
    write = 1  # nums[:write] holds the distinct values seen so far
    for read in range(1, len(nums)):
        if nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write

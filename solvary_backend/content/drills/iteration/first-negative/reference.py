def first_negative(nums) -> int | None:
    return next((n for n in nums if n < 0), None)

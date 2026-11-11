def euclid_steps(a: int, b: int) -> int:
    steps = 0
    while b:
        a, b = b, a % b
        steps += 1
    return steps

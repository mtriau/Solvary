from collections.abc import Callable


def fixed_point(
    f: Callable[[float], float], x: float, tol: float = 1e-9, max_steps: int = 1000
) -> float:
    for _ in range(max_steps):
        if abs((nxt := f(x)) - x) <= tol:
            return nxt
        x = nxt
    raise ValueError(f"no fixed point within {max_steps} steps")

from collections.abc import Callable


def fixed_point(
    f: Callable[[float], float], x: float, tol: float = 1e-9, max_steps: int = 1000
) -> float:
    """Iterate x = f(x) until it changes by at most tol; ValueError after max_steps."""
    raise NotImplementedError

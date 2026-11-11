from collections import deque
from collections.abc import Iterable


def moving_averages(values: Iterable[float], k: int) -> list[float]:
    window: deque[float] = deque(maxlen=k)
    out: list[float] = []
    for x in values:
        window.append(x)
        out.append(sum(window) / len(window))
    return out

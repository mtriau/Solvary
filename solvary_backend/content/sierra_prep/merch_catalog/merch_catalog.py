import time


def retry(
    fn,
    *,
    attempts: int = 5,
    base_delay: float = 0.1,
    factor: float = 2.0,
    max_delay: float = 2.0,
    timeout: float | None = None,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
    sleep=time.sleep,
    clock=time.monotonic,
):
    """Part 1: call `fn()` with exponential backoff. See the statement."""
    raise NotImplementedError

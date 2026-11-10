class TransientError(Exception):
    """The product API may raise this; the same request can be retried."""


def fetch_products(api, *, max_attempts: int = 5) -> list[dict]:
    """Part 1: every listing from a flaky, paginated product API. See the statement."""
    raise NotImplementedError

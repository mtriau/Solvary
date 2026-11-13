class RateLimiter:
    def __init__(self, tiers: dict[str, tuple[int, float]], default: str | None = None) -> None:
        """Part 1: tiers maps a tier name to (capacity, refill_per_second)."""
        raise NotImplementedError

    def set_client_tier(self, client_id: str, tier: str) -> None:
        raise NotImplementedError

    def allow(self, client_id: str, now: float) -> bool:
        raise NotImplementedError

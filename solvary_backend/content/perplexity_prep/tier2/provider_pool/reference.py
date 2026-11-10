"""Reference: LLM provider pool with priority routing and failover.

Shape: `providers: dict[name, _Provider]` with priority, capabilities,
consecutive-failure count, threshold and an insertion index. `route` is a
min over healthy providers that have the capability, keyed by
(priority, insertion_idx). O(P) per route; fine for a handful of providers.
"""


class _Provider:
    __slots__ = ("name", "priority", "capabilities", "threshold", "failures", "idx")

    def __init__(self, name: str, priority: int, capabilities: set[str],
                 threshold: int, idx: int) -> None:
        self.name = name
        self.priority = priority
        self.capabilities = set(capabilities)
        self.threshold = threshold
        self.failures = 0
        self.idx = idx

    @property
    def healthy(self) -> bool:
        return self.failures < self.threshold


class ProviderPool:
    """Priority routing with consecutive-failure health tracking. See PROBLEMS.md #1."""

    def __init__(self) -> None:
        self._providers: dict[str, _Provider] = {}
        self._next_idx = 0

    def add_provider(self, name: str, priority: int, capabilities: set[str],
                     failure_threshold: int = 3) -> None:
        # Re-adding replaces the entry outright: new priority, capabilities,
        # threshold, a failure count of zero, and a fresh insertion index.
        self._providers[name] = _Provider(name, priority, capabilities,
                                          failure_threshold, self._next_idx)
        self._next_idx += 1

    def route(self, capability: str) -> str | None:
        best = None
        for p in self._providers.values():
            if capability not in p.capabilities or not p.healthy:
                continue
            if best is None or (p.priority, p.idx) < (best.priority, best.idx):
                best = p
        return best.name if best is not None else None

    def _get(self, name: str) -> _Provider:
        try:
            return self._providers[name]
        except KeyError:
            raise ValueError(f"unknown provider {name!r}") from None

    def report_failure(self, name: str) -> None:
        self._get(name).failures += 1

    def report_success(self, name: str) -> None:
        self._get(name).failures = 0

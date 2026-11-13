from __future__ import annotations

import math
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass

EPS = 1e-9  # float tolerance when comparing tokens with a cost


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


class RateLimiter:
    def __init__(
        self,
        tiers: dict[str, tuple[int, float]],
        default: str | None = None,
        clock: Callable[[], float] | None = None,
        store: MutableMapping | None = None,
    ) -> None:
        self._tiers = dict(tiers)  # tier -> (capacity, refill_per_second)
        self._default = default
        self._clock = clock
        self._store = store if store is not None else {}  # (client, scope) -> _Bucket
        self._client_tier: dict[str, str] = {}
        self._rules: dict[tuple[str, str], tuple[int, float]] = {}  # (tier, scope) -> limits

    # ── Part 1 ─────────────────────────────────────────────────────

    def set_client_tier(self, client_id: str, tier: str) -> None:
        # Tokens are clamped lazily: every refill caps at the *current* capacity.
        self._client_tier[client_id] = tier

    def allow(self, client_id: str, now: float | None = None,
              scope: str | None = None, cost: float = 1) -> bool:
        if cost <= 0:
            raise ValueError("cost must be positive")
        buckets = self._buckets(client_id, scope, self._resolve(now))
        if buckets is None:
            return False
        ok = all(b.tokens + EPS >= cost for _, b, _, _ in buckets)
        for key, bucket, _, _ in buckets:
            if ok:  # all-or-nothing: only consume once every bucket agreed
                bucket.tokens = max(0.0, bucket.tokens - cost)
            self._store[key] = bucket  # write back: the store may copy values
        return ok

    # ── Part 2 ─────────────────────────────────────────────────────

    def update_tier(self, tier: str, capacity: int, refill_per_second: float) -> None:
        self._tiers[tier] = (capacity, refill_per_second)

    def remove_client(self, client_id: str) -> None:
        self._client_tier.pop(client_id, None)
        for key in [k for k in self._store if k[0] == client_id]:
            del self._store[key]

    # ── Part 3 ─────────────────────────────────────────────────────

    def tokens(self, client_id: str, now: float | None = None,
               scope: str | None = None) -> float:
        buckets = self._buckets(client_id, scope, self._resolve(now))
        if buckets is None:
            return 0.0
        for key, bucket, _, _ in buckets:
            self._store[key] = bucket
        return buckets[-1][1].tokens  # the scope bucket if there is one, else the base

    def retry_after(self, client_id: str, now: float | None = None,
                    scope: str | None = None, cost: float = 1) -> float:
        buckets = self._buckets(client_id, scope, self._resolve(now))
        if buckets is None:
            return math.inf
        wait = 0.0
        for _, bucket, capacity, rate in buckets:
            missing = cost - bucket.tokens
            if missing <= EPS:
                continue
            if cost > capacity or rate <= 0:
                return math.inf
            wait = max(wait, missing / rate)
        return wait

    # ── Part 4 ─────────────────────────────────────────────────────

    def add_rule(self, tier: str, scope: str, capacity: int, refill_per_second: float) -> None:
        self._rules[(tier, scope)] = (capacity, refill_per_second)

    # ── internals ──────────────────────────────────────────────────

    def _resolve(self, now: float | None) -> float:
        if now is not None:  # an explicit `now` wins over the clock
            return now
        if self._clock is None:
            raise ValueError("no `now` given and no clock configured")
        return self._clock()

    def _effective_tier(self, client_id: str) -> str | None:
        tier = self._client_tier.get(client_id)
        if tier not in self._tiers:
            tier = self._default
        return tier if tier in self._tiers else None  # None: fail closed

    def _buckets(self, client_id: str, scope: str | None, now: float):
        """Refilled (key, bucket, capacity, rate) for the base bucket and, when a
        rule exists, the scope bucket (last). None if the client is denied."""
        tier = self._effective_tier(client_id)
        if tier is None:
            return None
        limits = [(None, *self._tiers[tier])]
        if scope is not None and (tier, scope) in self._rules:
            limits.append((scope, *self._rules[(tier, scope)]))
        out = []
        for sc, capacity, rate in limits:
            key = (client_id, sc)
            bucket = self._store.get(key)
            if bucket is None:
                bucket = _Bucket(float(capacity), now)  # buckets start full
            else:
                elapsed = max(0.0, now - bucket.last_refill)  # time never runs backwards
                bucket.tokens = min(capacity, bucket.tokens + elapsed * rate)
                bucket.last_refill = max(bucket.last_refill, now)
            out.append((key, bucket, capacity, rate))
        return out

# Tiered Rate Limiter: Part 4

The same `RateLimiter` grows once more, and this is the escalation xAI and
Snowflake both reach: limits that depend on what is being requested, and then
more than one server. Your earlier tests still run.

### What to implement

- `add_rule(tier: str, scope: str, capacity: int, refill_per_second: float) -> None`:
  every client in `tier` gets an additional bucket for `scope` (for example
  `"url:/search"` or `"payload"`).
- `allow(client_id, now=None, scope=None, cost=1) -> bool`
- `tokens(client_id, now=None, scope=None) -> float`: the scope bucket's tokens
  if a rule exists for that scope, otherwise the base bucket's.
- `retry_after(client_id, now=None, scope=None, cost=1) -> float`
- `RateLimiter(tiers, default=None, clock=None, store=None)`: `store` is an
  optional `MutableMapping` that holds **all bucket state**.

### Rules

- A request passes only if it passes the client's **base bucket** (from its
  tier) **and**, when a rule exists for the request's `scope` in that tier, the
  **scope bucket**. A `scope` with no rule is checked against the base bucket
  only.
- It consumes `cost` tokens from **each** bucket it touches (payload-aware:
  for example the request body size in KB).
- **All-or-nothing:** if any bucket cannot cover `cost`, nothing is consumed
  from any bucket.
- A `cost` larger than a bucket's capacity is always denied. `cost <= 0`
  raises `ValueError`. `retry_after` is the slowest of the buckets involved and
  `math.inf` if any of them can never cover the cost.
- Scope buckets are per client, start full, and follow the same refill, clamp
  and backwards-time rules as the base bucket.
- **Shared store:** two limiters constructed with the same `store` are two
  "nodes" of one service and share the buckets, so the combined allowed count
  for a client never exceeds its capacity. Tier assignments and rules are
  configuration; each node is given its own. Without a `store`, a limiter keeps
  private state.

### Worked example

```python
limiter = RateLimiter({"pro": (100, 0.0)})
limiter.set_client_tier("a", "pro")
limiter.add_rule("pro", "payload", 50, 0.0)

limiter.allow("a", 0.0, scope="payload", cost=30)   # -> True
limiter.allow("a", 0.0, scope="payload", cost=30)   # -> False (20 left in scope)
limiter.tokens("a", 0.0)                            # -> 70.0   (base paid 30 once)

shared = {}
n1 = RateLimiter({"t": (5, 0.0)}, store=shared); n1.set_client_tier("a", "t")
n2 = RateLimiter({"t": (5, 0.0)}, store=shared); n2.set_client_tier("a", "t")
sum(n.allow("a", 0.0) for _ in range(10) for n in (n1, n2))   # -> 5
```

### Clarifications

- **Does a scoped request also cost the base bucket?** Yes, the same `cost`.
- **A real store may hand back copies.** Write bucket state back after you
  change it; do not rely on mutating an object you read.
- **Do the nodes need locking?** Not here; calls are sequential. Say how you
  would make check-and-decrement atomic (a Lua script or a compare-and-swap).
- **What if the nodes' clocks disagree?** The backwards-time rule applies to
  the shared bucket: an earlier time causes no refill and no error.
- **Adding a rule twice for one `(tier, scope)`?** The later call replaces it.

Run the provided tests with **Submit**.

---
Interviewer notes

Two traps: consuming from the first bucket before checking the second (a rejected request still costs tokens), and bucket state that lives in a mutable object the store may copy. For the distributed discussion expect: shared state in Redis with an atomic script, the clock-skew problem (use the store's time), and the alternative of local buckets with a periodic share of the global budget when strict accuracy is unnecessary. Keep to about 20 minutes; this is where the first-hand candidate ran out.

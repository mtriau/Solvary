# Tiered Rate Limiter: Part 2

The same `RateLimiter` grows. Operations need to change limits without a
restart: a customer upgrades, an incident calls for tighter free-tier limits.
Your earlier tests still run, so keep Part 1 working.

### What to implement

- `update_tier(tier: str, capacity: int, refill_per_second: float) -> None`:
  change (or create) a tier. It takes effect immediately for every client
  currently in that tier, including clients using it as the `default`.
- `remove_client(client_id: str) -> None`: forget the client's tier assignment
  and its bucket. Unknown ids are ignored.
- `set_client_tier` (existing) may now move a client between tiers.

### Rules

- **Capacity is only an upper bound; tokens do not jump.** After an update,
  each client's existing tokens are **clamped** to the new capacity: a raise
  grants nothing (the new headroom has to be earned by refilling), a cut
  truncates.
- The new refill rate applies from now on.
- **Moving a client to another tier keeps its current tokens**, clamped to the
  new tier's capacity. A move to a bigger tier does not refill the bucket.
- After `remove_client`, the client behaves as one never seen: its tier
  assignment is gone (default or denied) and a new bucket starts full.

### Worked example

```python
limiter = RateLimiter({"free": (3, 1.0), "pro": (10, 5.0)})
limiter.set_client_tier("a", "free")
limiter.allow("a", 0.0)               # -> True    (2 tokens left)
limiter.update_tier("free", 100, 1.0)
[limiter.allow("a", 0.0) for _ in range(3)]
# -> [True, True, False]             (the raise granted nothing)

limiter.update_tier("free", 1, 1.0)   # a cut: tokens clamp down to 1 at most
limiter.set_client_tier("a", "pro")   # keeps what it has, never more than 10
limiter.remove_client("a")
```

### Clarifications

- **Is the update applied when the client is next used, or immediately?** The
  observable result must be as if immediate. A lazy design is fine: clamp when
  refilling, since refills always cap at the current capacity.
- **Which time does the new rate apply to?** The tests call `update_tier` at
  the same moment as the client's last request, so "from now on" and "since
  the last request" coincide.
- **Can `update_tier` create a tier?** Yes. A client assigned to a tier name
  that did not exist (and was denied or on the default) uses the new tier once
  it exists.
- **A client I have never seen?** Its bucket is created on first use, full at
  the capacity current at that moment.
- **Can the rate be `0.0`?** Yes: the bucket never refills.

Run the provided tests with **Submit**.

---
Interviewer notes

The pitfall in this part is treating a capacity raise as a refill: capacity is a cap, not a balance, so tokens must not jump. Clamping at refill time (`min(capacity, tokens + elapsed x rate)`) gives the right answer for raises, cuts and tier moves with no scan over clients. Ask how the candidate would test it; Part 3 turns that into the real follow-up. Aim for about 10 minutes.

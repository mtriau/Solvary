# Tiered Rate Limiter: Part 1

Snowflake asks this as a 60-minute design-and-extend screen, and a candidate
who solved it reported being rejected for running out of time before the last
follow-up, so pacing is the point. Build a per-client rate limiter with
service tiers, and say the algorithm choice and its trade-offs out loud as you
code. Later parts make limits editable at runtime, put time under your
control, and then add compound rules and several nodes.

### What to implement

In `rate_limiter.py`:

- `RateLimiter(tiers: dict[str, tuple[int, float]], default: str | None = None)`
  where each tier maps to `(capacity, refill_per_second)`.
- `set_client_tier(client_id: str, tier: str) -> None`
- `allow(client_id: str, now: float) -> bool`: consume one token and return
  `True` if the client has one, otherwise return `False` and consume nothing.

### Rules

- Use a **token bucket** per client. Buckets start **full**.
- Tokens accrue continuously: after `elapsed` seconds a bucket gains
  `elapsed * refill_per_second` tokens (fractions count), never above
  `capacity`.
- A request costs one token; a bucket needs at least 1 token to allow it.
- For one client, calls arrive with non-decreasing `now` (see Clarifications
  for what happens if they do not).
- A client with **no tier**, or a tier name that is **not in `tiers`**, uses
  the `default` tier if one is given and known. Otherwise the request is
  **denied** (fail closed).

### Worked example

```python
limiter = RateLimiter({"free": (3, 1.0), "pro": (10, 5.0)})
limiter.set_client_tier("alice", "free")
[limiter.allow("alice", 0.0) for _ in range(4)]
# -> [True, True, True, False]     (burst of 3, then empty)
limiter.allow("alice", 1.0)    # -> True   (1 s x 1 token/s)
limiter.allow("alice", 1.0)    # -> False

limiter.allow("ghost", 0.0)    # -> False  (no tier, no default)
RateLimiter({"free": (3, 1.0)}, default="free").allow("ghost", 0.0)  # -> True
```

### Clarifications

- **Do buckets start full?** Yes. A new client may burst up to `capacity`
  immediately.
- **Does a denied request cost anything or delay the refill?** No. Denials
  consume nothing, and the refill is always `elapsed x rate` measured from the
  last time the bucket was updated.
- **Float tolerance?** Compare with a tiny tolerance (about `1e-9`), so that
  `0.5 s x 2/s` counts as exactly one token.
- **What if `now` goes backwards for one client?** No refill and no error: the
  call is judged on the tokens it already has, and later refills are measured
  from the latest time that client was ever seen.
- **Unknown tier names?** Treated like no tier: default if given, else denied.
  A `default` that is not itself a key of `tiers` also fails closed.
- **Are different clients independent?** Yes, one bucket per client.

Run the provided tests with **Submit**.

---
Interviewer notes

Token bucket gives O(1) time and memory per client and allows bursts up to capacity; a sliding-window log is exact but stores one timestamp per request, and a fixed window lets double-sized bursts through at window edges. Listen for the candidate stating that choice early. Refill is `elapsed x rate` from a stored `last_refill`, not a timer thread, and the bucket never exceeds capacity. Part 1 should take about 15 minutes; the first-hand candidate lost the screen on time, so move on.

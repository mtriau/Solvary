# Tiered Rate Limiter: Part 3

The same `RateLimiter` grows. Snowflake's follow-up was: "the real clock makes
refill hard to test, how do you handle time?" Make time injectable and make the
limiter observable. Your earlier tests still run, and the Part 3 tests use a
fake clock that steps deterministically, with no sleeping.

### What to implement

- `RateLimiter(tiers, default=None, clock=None)`, where `clock` is an optional
  `Callable[[], float]` returning the current time in seconds.
- `allow(client_id, now=None) -> bool`: with `now` omitted it reads `clock()`.
- `tokens(client_id, now=None) -> float`: the client's current tokens after
  refilling to that time, without consuming anything.
- `retry_after(client_id, now=None) -> float`: seconds until one token is
  available; `0.0` if one is available now.

### Rules

- **Explicit `now` wins.** If `now` is given, the clock is not consulted at
  all. If `now` is omitted and there is no clock, raise `ValueError`.
- Explicit times and the clock may be mixed. They follow the same rule as
  before: a time earlier than the latest one seen for that client causes no
  refill and no error.
- `tokens` and `retry_after` never consume. Reading them repeatedly changes
  nothing.
- `tokens` is `0.0` for a client that would be denied (no tier, no default).
- `retry_after` is `(1 - tokens) / refill_per_second` when below one token,
  `0.0` when a token is available, and `math.inf` when it can never become
  available (zero refill rate, or a client that is always denied).

### Worked example

```python
class FakeClock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now

clock = FakeClock()
limiter = RateLimiter({"t": (2, 0.5)}, clock=clock)
limiter.set_client_tier("c", "t")
limiter.allow("c"), limiter.allow("c")   # -> (True, True)
limiter.allow("c")                       # -> False
limiter.retry_after("c")                 # -> 2.0
clock.now = 0.5
limiter.tokens("c")                      # -> 0.25
limiter.retry_after("c")                 # -> 1.5
limiter.allow("c", now=2.0)              # -> True   (explicit now wins)
```

### Clarifications

- **Which wins when both are available?** The explicit `now`.
- **Does `tokens` on a brand-new client create a bucket?** It reports a full
  bucket at the client's capacity, and it has no other visible effect.
- **Float comparisons?** Use tolerances in your own tests; the limiter itself
  allows a request when tokens are within about `1e-9` of the cost.
- **Will waiting exactly `retry_after` seconds make `allow` succeed?** Yes,
  and waiting noticeably less will not.
- **Is the clock called once per operation?** At most once; the tests do not
  rely on the number of calls except that an explicit `now` means zero calls.

Run the provided tests with **Submit**.

---
Interviewer notes

Hear the candidate say why injection beats patching `time.time` or sleeping: tests become exact, instant and repeatable. A default of `time.monotonic` is the right production choice because wall clocks jump. Check that refill is still `elapsed x rate` and that `retry_after` handles the zero-rate and fail-closed cases. Budget about 15 minutes, which leaves 20 for the last follow-up that sank the first-hand candidate.

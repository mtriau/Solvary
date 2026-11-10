# LLM provider pool with failover

Route requests across external LLM providers by priority, track health,
fail over when a provider is down.

```python
pool = ProviderPool()
pool.add_provider("openai", priority=1, capabilities={"chat", "embed"})
pool.add_provider("anthropic", priority=2, capabilities={"chat"})
pool.add_provider("local", priority=3, capabilities={"chat", "embed"})

pool.route("chat")            # -> "openai"   (lowest priority number, healthy)
pool.report_failure("openai")
pool.report_failure("openai")
pool.report_failure("openai") # 3 consecutive failures -> unhealthy
pool.route("chat")            # -> "anthropic"
pool.route("embed")           # -> "local"    (anthropic lacks it)
pool.report_success("openai") # resets its failure count and marks healthy
pool.route("chat")            # -> "openai"
pool.route("video")           # -> None       (no provider can serve it)
```

- `add_provider(name, priority, capabilities, failure_threshold=3)`.
  Re-adding a name replaces it (new priority, capabilities and threshold)
  and resets its health.
- `route(capability) -> str | None`: the healthy provider with the lowest
  priority number that has the capability; ties by insertion order. None
  when no healthy provider has it (including when every capable provider
  is unhealthy).
- `report_failure(name)` / `report_success(name)`: consecutive-failure
  counting; a provider is unhealthy once it has `failure_threshold`
  consecutive failures (exactly N, not N+1); a success resets the count to
  zero. Either call with an unknown name raises ValueError.
- Likely follow-up: cooldown (unhealthy providers recover after N seconds,
  inject a clock), round-robin among equal priorities, per-provider rate
  limits.

### Why this is idiomatic

- EAFP, "easier to ask forgiveness than permission": attempt the lookups and handle the failure once, rather than guarding each step with `isinstance` and `in`. The guard version has to anticipate every way a step can fail; the `except` just lists the exceptions.
- Catching a tuple of *specific* exceptions keeps real bugs visible. A bare `except:` or `except Exception` would swallow typos in your own code.
- `*path` collects the steps as varargs, so the call site reads like a path; `default` is keyword-only because it comes after `*path`, which prevents it being mistaken for a step.
- The loop rebinds `data` as it descends. That is fine for a local name and avoids a second variable.

### The habit

When "might fail" means a normal exception, write the straight-line code in a `try` and catch exactly those exceptions.

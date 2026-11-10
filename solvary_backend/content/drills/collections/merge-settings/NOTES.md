### Why this is idiomatic

- `defaults | other` builds a new dict with the right-hand side winning. It never touches either input, unlike `defaults.update(overrides)`, which mutates the caller's dict. `{**defaults, **other}` is the same idea for older Python.
- The filter is `value is not None`, not `if value`. `0`, `""` and `False` are legitimate settings; only `None` means "unset". Truthiness is the wrong test here and the suite checks for it.
- One expression, no temporary `result = dict(defaults)` followed by a loop.

### The habit

Compare to `None` with `is not None` whenever falsy values are meaningful. And prefer operators that return new objects over methods that mutate arguments.

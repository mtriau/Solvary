### Why this is idiomatic

- `splitlines()` handles `\n`, `\r\n` and a trailing newline without producing a phantom empty last line (`split("\n")` would).
- The walrus operator `(line := raw.strip())` binds the stripped line inside the comprehension's filter so you strip once and use the result twice, in the truthiness check and in `startswith`. Before 3.8 you had to strip twice or fall back to a loop.
- Truthiness again: `if (line := ...)` is false for blank lines.
- If the walrus feels too clever for your team, the equivalent loop with `continue` statements is fine. The thing to avoid is `strip()` three times.

### The habit

When a filter needs a computed value and the body needs the same value, the walrus lets you compute it once without leaving the comprehension.

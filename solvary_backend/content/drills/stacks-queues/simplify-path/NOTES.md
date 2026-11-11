### Why this is idiomatic

- `split("/")` does the tokenising; empty parts fall out naturally and are skipped with the same `continue` as `"."`. No regex, no manual index walking.
- The stack is the directory you are "in". `..` pops it, guarded by `if stack` so the root has no parent. Everything else is a name and gets pushed, which is why `...` is handled correctly with no extra rule.
- `"/" + "/".join(stack)` handles the empty stack (`"/"`) and the non-empty one with the same expression.

### The habit

Tokenise with `split`, filter with `continue` at the top of the loop, and let a stack hold "where I am". Rebuild with `join`, never with string concatenation in the loop.

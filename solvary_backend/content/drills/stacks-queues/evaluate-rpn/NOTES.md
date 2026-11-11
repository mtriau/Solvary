### Why this is idiomatic

- A dispatch dict (`OPS[tok](a, b)`) replaces an `if/elif` chain and makes adding an operator a one-line change. The `operator` module has the arithmetic functions already named.
- `b, a = stack.pop(), stack.pop()` pops in the right order and names the operands so `a - b` reads correctly. Getting this backwards is the classic slip, hence the subtraction test.
- `int(a / b)` truncates toward zero; `//` floors, so `7 // -3 == -3`. Know the difference and say it when you write it.
- `tok in OPS` distinguishes operators from numbers, so `"-4"` is parsed as a number without any extra check.

### The habit

"Postfix" or "undo the last thing" means a stack. "Pick behaviour by a token" means a dict of callables, not a chain of `elif`.

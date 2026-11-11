### Why this is idiomatic

- `iter(callable, sentinel)` exists for exactly this: polling a function until a stop value. `for chunk in iter(partial(f.read, 4096), b""):` is the classic use.
- The hand-written loop has a well-known awkward shape (`while True: line = read(); if line == sentinel: break`). The walrus fixes it: `while (line := read()) != sentinel: out.append(line)`. Assign and test in the condition, so the exit is in one place.
- "Do not read past the sentinel" is the real requirement; both forms honour it because the test happens immediately after each read.

### The habit

When the value you test is produced by the same call that advances the loop, put the call in the condition (walrus) or use two-argument `iter`. Never read once before the loop and again at the bottom.

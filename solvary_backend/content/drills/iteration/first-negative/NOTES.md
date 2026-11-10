### Why this is idiomatic

- `next(iterator, default)` returns the first item or the default, and stops the moment it has one. The generator expression inside it is lazy, so nothing after the match is evaluated. The suite verifies that with a generator that explodes if read too far.
- The loop-with-`return` version is also fine Python. What is *not* fine is `[n for n in nums if n < 0][0]`, which builds the whole list, and then crashes on empty input.
- `None` as "not found" is conventional for a function that returns a value; raising would be the alternative if callers should never miss.

### The habit

"The first element that..." is `next(... , default)` over a generator expression.

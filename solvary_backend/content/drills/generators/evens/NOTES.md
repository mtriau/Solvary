### Why this is idiomatic

- A generator function produces values on demand. `while True: yield n` is a perfectly normal infinite sequence in Python because nothing runs until the consumer asks for the next item.
- `itertools.count(0, 2)` is the one-line standard-library version and equally acceptable; the suite accepts any iterator that yields the right values.
- The consumer controls how much to take with `islice`. The producer never needs a `limit` parameter.

### The habit

When a function would build a list only for the caller to loop over it, make it a generator. When the sequence has no natural end, that is the only option.

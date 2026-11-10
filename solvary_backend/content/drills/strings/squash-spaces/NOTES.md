### Why this is idiomatic

- `str.split()` with no argument splits on runs of any whitespace and discards empty pieces, which is exactly "collapse and trim". `split(" ")` would keep empty strings between consecutive spaces.
- `" ".join(...)` reassembles with single spaces. The pair is a well-known Python idiom; readers recognise it on sight.
- A regex `re.sub(r"\s+", " ", text).strip()` also works, but it is a second tool for a job the string methods already do.

### The habit

Know what `split()` without arguments does. It solves a surprising number of "clean up this text" tasks.

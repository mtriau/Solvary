### Why this is idiomatic

- `Counter(iterable)` counts in one call; `most_common(n)` sorts by count descending and, for ties, keeps insertion order. That is the whole problem.
- The hand-rolled version (`counts = {}`, `counts[w] = counts.get(w, 0) + 1`, then `sorted(counts.items(), key=..., reverse=True)[:n]`) is five lines that re-implement the standard library.
- `text.lower().split()` normalises and tokenises in one chain of method calls.

### The habit

Counting things? `Counter`. Before writing `.get(key, 0) + 1`, remember it exists.

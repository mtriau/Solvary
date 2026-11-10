# Markdown Chunker: Part 1

Help-center articles are indexed for retrieval in chunks. Split a document
into chunks that each fit a size limit, without ever cutting a line in two.

### What to implement

`split_markdown(markdown: str, max_size: int) -> list[str]`

### Rules

1. **Lines** are the pieces you get from splitting the document on `"\n"`
   (exactly that character; do not use `splitlines()` or strip anything). A
   blank line is a line of length 0.
2. **A chunk is some consecutive lines joined back with `"\n"`.** Its size
   is the length of that joined string. So two lines of 3 characters make a
   chunk of size 7, because the newline between them counts. A chunk has no
   trailing newline.
3. **Pack greedily, in order.** Keep adding the next line to the current
   chunk while the chunk's size stays `<= max_size`. When the next line
   would push it over, close the chunk and start a new one with that line.
4. Every line appears in exactly one chunk, in document order, so
   `"\n".join(chunks) == markdown`.
5. `split_markdown("", n) -> []`.
6. Guarantee: no single line is longer than `max_size`.

### Worked example

```python
split_markdown("aaa\nbbb\nccc\nddd", 7)    # -> ["aaa\nbbb", "ccc\nddd"]
split_markdown("aaa\nbbb\nccc\nddd", 6)    # -> ["aaa", "bbb", "ccc", "ddd"]
split_markdown("aaa\nbbb", 100)            # -> ["aaa\nbbb"]
```

With a limit of 7: `"aaa"` is 3; adding `"bbb"` gives `"aaa\nbbb"`, size 7,
which still fits; adding `"ccc"` would make size 11, so the chunk closes and
`"ccc"` starts the next one. With a limit of 6, `"aaa\nbbb"` is already 7,
so every line ends up alone.

### Clarifications

- **Does the newline count toward the size?** Yes, every newline *between*
  two lines of a chunk counts. There is no newline after the last line of a
  chunk.
- **Balanced chunks, or as full as possible?** Greedy: fill each chunk as
  far as it goes before starting the next. `"a\nb\nc\nd\ne"` with limit 5 is
  `["a\nb\nc", "d\ne"]`, not two chunks of 2 and 3 lines.
- **How do blank lines behave?** They are ordinary lines of length 0.
  `"a\n\nb"` with limit 3 gives `["a\n", "b"]`: `"a"` plus the empty line is
  `"a\n"` (size 2), and adding `"b"` would make 4.
- **The document ends with `"\n"`?** Then its last line is an empty string.
  Treat it like any other line.
- **A line longer than `max_size`?** Guaranteed not to happen. If you want
  to be defensive, put such a line in a chunk of its own.
- **Exactly at the limit?** Fits. A chunk of size `max_size` is fine.

Run the provided tests with **Submit**; later parts come with their own test
files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

---
Interviewer notes

Two candidates reported this Software Engineer phone screen in April and
May 2026 ("split a markdown file into chunks under a size limit, carrying
the previous headers into new chunks"). Part 1 is the plain chunker; the
header rule is Part 2. Watch for off-by-one on the joining newline.

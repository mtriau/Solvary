# Markdown Chunker: Part 2

A chunk that starts in the middle of a section loses its context: a reader
(or a retrieval model) cannot tell which article and section it came from.
Repeat the section's headers at the top of such chunks.

### Definitions

- A **header** is a line that starts, at column 0, with one to six `#`
  characters followed by a space. Its **level** is the number of `#`.
  `#tag` (no space) and `####### x` (seven `#`) are not headers.
- **Active headers.** Scan the document from the top, keeping a stack of
  headers. When you meet a header of level `L`, it removes every active
  header of level `L` or deeper, then becomes active. The active headers at
  any point are therefore a chain in strictly increasing level order, such
  as `# A`, `## B`, `### C`.

### What changes

Extend `split_markdown(markdown, max_size)`:

1. Packing is still greedy, line by line, as in Part 1.
2. **When a new chunk starts** (every chunk except the first), it begins
   with the active headers, each as its own line, in level order, **before**
   the line that triggered the new chunk.
3. **If the triggering line is itself a header,** first apply it to the
   stack (it clears same-or-deeper headers), then repeat only its
   **parents**, the active headers of lower level. Never write that header
   twice.
4. The repeated header lines count toward the chunk's size like any other
   line.
5. Guarantee: every line, plus its active headers, fits in `max_size`.

### Worked example

```python
split_markdown("# T\nHello\n## S\nWorld", 100)
# -> ["# T\nHello\n## S\nWorld"]

split_markdown("# A\n## B\nxxxx\n## C\nyyyy", 13)
# -> ["# A\n## B\nxxxx", "# A\n## C\nyyyy"]     "## C" repeats only "# A"
```

Second example, limit 13: `"# A\n## B\nxxxx"` is exactly 13. `"## C"` does
not fit, so a new chunk starts with it. `## C` is level 2, so it replaces
`## B`; its only parent is `# A`. The new chunk opens as `"# A\n## C"`
(size 8), and `"yyyy"` brings it to 13.

Another one, limit 12: `"# T\na\nb\n## S\nc\nd"` gives
`["# T\na\nb\n## S", "# T\n## S\nc\nd"]`. The line `"c"` triggers the new
chunk; it is not a header, so the whole active chain `# T`, `## S` is
repeated above it.

### Clarifications

- **Does the first chunk get headers repeated?** No. It starts with the
  document's first line.
- **A header line fits in the current chunk. Anything special?** No. It is
  added like any line, and it updates the active headers.
- **A lower-level header appears later, say `# D` after `# A`, `## B`,
  `### C`.** It clears all three (level 1 and deeper) and becomes the only
  active header. A chunk starting after it begins with `# D` alone.
- **Same-level header?** `## C` after `## B` replaces `## B` (and anything
  deeper). `# A` stays.
- **Is the repeated header text exactly the original line?** Yes, character
  for character.
- **How deep can the chain be?** Up to six levels. All of them are repeated,
  in order.
- **Does a repeated header change the active-header stack?** No. The stack
  is driven only by the document's own lines.
- **Document with no headers?** Behaves exactly as Part 1.

Run the provided tests with **Submit**.

---
Interviewer notes

The candidate who reported this "second-guessed the header-prepending
step" and found the edge cases the interesting part: a header of a lower
level clearing deeper ones, a chunk that starts with a header, and the
repeated headers counting toward size.

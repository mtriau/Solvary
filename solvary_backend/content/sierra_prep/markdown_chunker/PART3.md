# Markdown Chunker: Part 3

Articles contain code samples. A code block must never be cut in half, and
a `#` inside one is not a header.

### Definitions

- A **fence line** is any line that starts with three backticks
  (`` ``` ``) at column 0. The opening fence may carry a language tag
  (`` ```python ``).
- A **fenced block** runs from an opening fence line through the next fence
  line (the closing one), both included. A fence that is never closed runs
  to the end of the document.

### What changes

Extend `split_markdown(markdown, max_size)`:

1. **A fenced block is atomic.** Treat the whole block (opening line
   through closing line) as one unit that is placed into a chunk whole. Its
   size is its lines joined with `"\n"`, like any group of lines.
2. Packing is still greedy: if the current chunk plus the block fits,
   append the block; otherwise close the chunk and start a new one with the
   active headers (Part 2) followed by the block.
3. Lines inside a fence are never headers and never change the active
   headers, even if they start with `# `.
4. Guarantee: every fenced block, plus its active headers, fits in
   `max_size`.

### Worked example

```python
split_markdown("# A\nline\n```\ncode1\ncode2\n```\ntail", 24)
# -> ["# A\nline", "# A\n```\ncode1\ncode2\n```", "# A\ntail"]
```

Limit 24. `"# A\nline"` is 8. The block (fence, `code1`, `code2`, fence) is
19; adding it would make 28, so a new chunk starts: `# A` plus the block is
23. `"tail"` would make 28, so it gets its own chunk with `# A` repeated.

### Clarifications

- **The block's lines would fit one by one, but not as a whole. Can I split
  it?** No. `"h\n```\n1\n2\n3\n```"` with limit 12 is
  `["h", "```\n1\n2\n3\n```"]`.
- **What exactly opens and closes a fence?** Any line starting with three
  backticks. Text after the backticks is allowed on either line and does not
  matter.
- **Two blocks back to back?** Separate units. The line right after a
  closing fence that itself starts with backticks opens a new block.
- **An unclosed fence?** Everything from the opening line to the end of the
  document is one block.
- **Do headers before and after a fence still work?** Yes. The active
  headers at a block are whatever was active when its opening line was
  reached, and a header after the closing fence updates the stack normally.
- **Is a fence line indented by spaces a fence?** No. Only at column 0.

Run the provided tests with **Submit**.

---
Interviewer notes

Part 3 is an extension in the spirit of the reported problem (RAG
chunking of help-center content), not a reported part. It tests whether
the Part 2 code was written around "units" that can be bigger than a
line, or has to be restructured.

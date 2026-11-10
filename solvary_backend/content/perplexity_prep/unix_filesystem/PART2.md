# In-Memory Unix File System: Part 2

Add to `FileSystem`:

- `rm(path)`: remove a file. Error if missing or if it is a directory.
- `rmdir(path)`: remove an EMPTY directory. Error if missing, a file,
  non-empty, or the root.
- `run(line: str) -> str`: a command runner. `line` is one command:
  `"mkdir /a"`, `"touch /a/f"`, `"rm /a/f"`, `"rmdir /a"`, `"read /a/f"`,
  `"ls /a"`, `"write /a/f the content, which may contain spaces"`.
  `read` returns the content; `ls` returns the names joined by a single
  space; everything else returns `""`. Unknown command: raise.

Pinned details:

- `write` content is the rest of the line verbatim after the path: inner
  and trailing spaces are preserved (`line.split(" ", 2)` semantics).
  `"write /a/f"` with no content writes `""` (and creates the file).
- `"ls /"` on an empty directory returns `""`.
- Unknown command raises `ValueError`. Errors from the underlying operation
  propagate unchanged.
- Same error contract as Part 1: an OSError subclass or ValueError, and a
  failed operation leaves the file system unchanged.

Run the provided tests: `pytest unix_filesystem -q`.

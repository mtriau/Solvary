# In-Memory Unix File System: Part 3

Add to `FileSystem`:

- `cd(path)`: change the current directory. `pwd() -> str` returns it as
  an absolute path (`"/"` for root).
- Every method now accepts relative paths, resolved against the current
  directory: `"docs/a.txt"`, `"./docs"`, `"../shared/b.txt"`, `".."`.
- `".."` at the root stays at the root. Repeated slashes (`"a//b"`) and a
  trailing slash (`"docs/"`) are tolerated. `"."` is a no-op segment.
- cd to a missing path or to a file fails and leaves the current
  directory unchanged.

Pinned details:

- `pwd()` has no trailing slash except for the root: `"/a/b"`, not `"/a/b/"`.
- `run()` commands also accept relative paths. Add `"cd <path>"` (returns
  `""`) and `"pwd"` (returns the path) to `run`.
- `""` as a path is not tested. rmdir of the current directory is not
  tested; state your choice.
- Same error contract as before: an OSError subclass or ValueError, and a
  failed operation leaves the file system and the cwd unchanged.

Run the provided tests: `pytest unix_filesystem -q`.

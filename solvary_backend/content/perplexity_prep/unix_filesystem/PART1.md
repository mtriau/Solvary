# In-Memory Unix File System: Part 1

Implement `FileSystem`, an in-memory tree of directories and files. Paths
are absolute (`"/a/b/c"`); `"/"` is the root and always exists. No `.`,
`..`, or relative paths in this part.

- `mkdir(path: str) -> None`
  Create a directory. **Strict**, not `mkdir -p`: every parent must already
  exist, and only the last component is created. Error if the target
  already exists (as a file or a directory).
- `touch(path: str) -> None`
  Create an empty file. Parent directory must exist. No-op if the file
  already exists; error if the path is a directory.
- `write(path: str, content: str) -> None`
  Append `content` to a file, creating the file if it does not exist
  (parent must exist). Error if the path is a directory.
- `read(path: str) -> str`
  Return a file's contents. Error if missing or a directory.
- `ls(path: str) -> list[str]`
  If `path` is a directory, return the **sorted** names of its entries.
  If `path` is a file, return `[name]`. Error if missing.

A failed operation must leave the file system unchanged.

```python
fs = FileSystem()
fs.mkdir("/a")
fs.mkdir("/a/b")
fs.write("/a/b/notes.txt", "hello")
fs.write("/a/b/notes.txt", " world")
fs.touch("/a/z.txt")
fs.read("/a/b/notes.txt")      # -> "hello world"
fs.ls("/a")                    # -> ["b", "z.txt"]
fs.ls("/a/b/notes.txt")        # -> ["notes.txt"]
fs.ls("/")                     # -> ["a"]
fs.mkdir("/x/y")               # error: /x does not exist
```

Error contract: every error raises either an `OSError` subclass
(`FileNotFoundError`, `FileExistsError`, `NotADirectoryError`,
`IsADirectoryError`, or plain `OSError`) or `ValueError`. The provided tests
accept either convention; pick one and be consistent. Never return `False`
or `None` to signal an error.

Run the provided tests: `pytest unix_filesystem -q`. Later parts come with
their own test files.

*(Further parts will be revealed by the interviewer as you complete each stage.)*

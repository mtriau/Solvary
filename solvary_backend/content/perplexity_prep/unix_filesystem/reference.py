"""Ideal solution: In-Memory Unix File System, all three parts.

Part 1: strict mkdir / touch / write / read / ls over absolute paths.
Part 2: rm / rmdir and a thin `run(line)` command dispatcher.
Part 3: cd / pwd and relative paths (".", "..", repeated and trailing
        slashes) resolved against a cwd stored as a component list.

Shape: one Node class (a directory holds `children`, a file holds
`content`). ONE `_parts(path)` normalizer turns any path, absolute or
relative, into absolute components. `_resolve(parts)` walks the tree and
`_parent_and_name(path)` splits off the last component for the creating
and deleting operations. Every public method is a few lines over those
three helpers. Every op validates before it mutates, so a raised error
leaves the tree untouched.

Error contract: OSError subclasses. FileNotFoundError for a missing node,
FileExistsError for a target that already exists, NotADirectoryError when
a directory was needed, IsADirectoryError when a file was needed, plain
OSError for rmdir of a non-empty directory or of the root. `run` raises
ValueError for an unknown command.
"""


class Node:
    __slots__ = ("name", "children", "content")

    def __init__(self, name: str, is_dir: bool) -> None:
        self.name = name
        self.children: dict[str, "Node"] | None = {} if is_dir else None
        self.content = "" if not is_dir else None

    @property
    def is_dir(self) -> bool:
        return self.children is not None


class FileSystem:
    def __init__(self) -> None:
        self.root = Node("/", True)
        self.cwd: list[str] = []          # absolute components, [] is root

    # ------------------------------------------------------------ helpers

    def _parts(self, path: str) -> list[str]:
        """Normalize `path` to absolute components. Relative paths start
        from cwd; "." and "" (repeated or trailing slash) are skipped;
        ".." pops, and at the root it stays at the root."""
        parts = [] if path.startswith("/") else list(self.cwd)
        for seg in path.split("/"):
            if seg in ("", "."):
                continue
            if seg == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(seg)
        return parts

    def _resolve(self, parts: list[str]) -> Node:
        node = self.root
        for seg in parts:
            if not node.is_dir:
                raise NotADirectoryError("/" + "/".join(parts))
            if seg not in node.children:
                raise FileNotFoundError("/" + "/".join(parts))
            node = node.children[seg]
        return node

    def _parent_and_name(self, path: str) -> tuple[Node, str]:
        """Parent directory node and the final component. The root has
        no parent, so a path that normalizes to the root raises."""
        parts = self._parts(path)
        if not parts:
            raise OSError("operation not permitted on the root")
        parent = self._resolve(parts[:-1])
        if not parent.is_dir:
            raise NotADirectoryError("/" + "/".join(parts[:-1]))
        return parent, parts[-1]

    def _file_at(self, path: str) -> Node:
        node = self._resolve(self._parts(path))
        if node.is_dir:
            raise IsADirectoryError(path)
        return node

    # ------------------------------------------------------------- Part 1

    def mkdir(self, path: str) -> None:
        parent, name = self._parent_and_name(path)
        if name in parent.children:
            raise FileExistsError(path)
        parent.children[name] = Node(name, True)

    def touch(self, path: str) -> None:
        parent, name = self._parent_and_name(path)
        existing = parent.children.get(name)
        if existing is None:
            parent.children[name] = Node(name, False)
        elif existing.is_dir:
            raise IsADirectoryError(path)

    def write(self, path: str, content: str) -> None:
        parent, name = self._parent_and_name(path)
        node = parent.children.get(name)
        if node is None:
            node = parent.children[name] = Node(name, False)
        elif node.is_dir:
            raise IsADirectoryError(path)
        node.content += content

    def read(self, path: str) -> str:
        return self._file_at(path).content

    def ls(self, path: str) -> list[str]:
        node = self._resolve(self._parts(path))
        return sorted(node.children) if node.is_dir else [node.name]

    # ------------------------------------------------------------- Part 2

    def rm(self, path: str) -> None:
        parent, name = self._parent_and_name(path)
        node = parent.children.get(name)
        if node is None:
            raise FileNotFoundError(path)
        if node.is_dir:
            raise IsADirectoryError(path)
        del parent.children[name]

    def rmdir(self, path: str) -> None:
        parent, name = self._parent_and_name(path)
        node = parent.children.get(name)
        if node is None:
            raise FileNotFoundError(path)
        if not node.is_dir:
            raise NotADirectoryError(path)
        if node.children:
            raise OSError(f"directory not empty: {path}")
        del parent.children[name]

    def run(self, line: str) -> str:
        """Parse one command line and dispatch. Parsing only; the tree
        logic lives in the public methods."""
        pieces = line.split(" ", 2)
        cmd = pieces[0]
        if cmd == "pwd":
            return self.pwd()
        if len(pieces) < 2:
            raise ValueError(f"missing path: {line!r}")
        path = pieces[1]
        if cmd == "write":
            content = pieces[2] if len(pieces) > 2 else ""
            self.write(path, content)
            return ""
        if cmd == "read":
            return self.read(path)
        if cmd == "ls":
            return " ".join(self.ls(path))
        simple = {
            "mkdir": self.mkdir, "touch": self.touch,
            "rm": self.rm, "rmdir": self.rmdir, "cd": self.cd,
        }
        if cmd not in simple:
            raise ValueError(f"unknown command: {cmd!r}")
        simple[cmd](path)
        return ""

    # ------------------------------------------------------------- Part 3

    def cd(self, path: str) -> None:
        parts = self._parts(path)
        if not self._resolve(parts).is_dir:
            raise NotADirectoryError(path)
        self.cwd = parts

    def pwd(self) -> str:
        return "/" + "/".join(self.cwd)


if __name__ == "__main__":
    def raises(fn) -> bool:
        try:
            fn()
        except (OSError, ValueError):
            return True
        return False

    # part 1
    fs = FileSystem()
    fs.mkdir("/a"); fs.mkdir("/a/b")
    fs.write("/a/b/notes.txt", "hello"); fs.write("/a/b/notes.txt", " world")
    fs.touch("/a/z.txt")
    assert fs.read("/a/b/notes.txt") == "hello world"
    assert fs.ls("/a") == ["b", "z.txt"]
    assert fs.ls("/a/b/notes.txt") == ["notes.txt"]
    assert fs.ls("/") == ["a"]
    assert raises(lambda: fs.mkdir("/x/y")) and fs.ls("/") == ["a"]
    assert raises(lambda: fs.mkdir("/a")) and raises(lambda: fs.mkdir("/"))
    assert raises(lambda: fs.mkdir("/a/z.txt/q"))
    assert raises(lambda: fs.touch("/a/b")) and raises(lambda: fs.touch("/"))
    fs.touch("/a/b/notes.txt"); assert fs.read("/a/b/notes.txt") == "hello world"
    assert raises(lambda: fs.write("/a", "x")) and raises(lambda: fs.read("/a"))
    assert raises(lambda: fs.read("/a/nope")) and raises(lambda: fs.ls("/nope"))
    assert raises(lambda: fs.ls("/a/z.txt/deeper"))

    # part 2
    assert raises(lambda: fs.rm("/a")) and raises(lambda: fs.rm("/a/nope"))
    fs.rm("/a/z.txt"); assert fs.ls("/a") == ["b"]
    assert raises(lambda: fs.rmdir("/a")) and fs.ls("/") == ["a"]
    assert raises(lambda: fs.rmdir("/")) and raises(lambda: fs.rmdir("/a/b/notes.txt"))
    fs.rm("/a/b/notes.txt"); fs.rmdir("/a/b"); assert fs.ls("/a") == []
    assert fs.run("mkdir /a/c") == "" and fs.run("write /a/c/f hello   world") == ""
    assert fs.run("read /a/c/f") == "hello   world"
    assert fs.run("write /a/c/f  tail ") == "" and fs.run("read /a/c/f") == "hello   world tail "
    assert fs.run("ls /a/c") == "f" and fs.run("ls /") == "a"
    assert fs.run("write /a/g") == "" and fs.run("read /a/g") == ""
    assert fs.run("touch /a/h") == "" and fs.run("ls /a") == "c g h"
    assert fs.run("rm /a/h") == "" and fs.run("ls /a") == "c g"
    assert raises(lambda: fs.run("rmdir /a/c")) and fs.run("ls /a/c") == "f"
    assert fs.run("rm /a/c/f") == "" and fs.run("rmdir /a/c") == "" and fs.run("ls /a") == "g"
    assert raises(lambda: fs.run("frobnicate /a")) and raises(lambda: fs.run("read /zzz"))
    assert FileSystem().run("ls /") == ""

    # part 3
    fs = FileSystem(); fs.mkdir("/a"); fs.mkdir("/a/b")
    assert fs.pwd() == "/"
    fs.cd("/a/b"); assert fs.pwd() == "/a/b"
    fs.mkdir("../c"); assert fs.ls("/a") == ["b", "c"]
    fs.cd("../../.."); assert fs.pwd() == "/"
    fs.cd("/a/b"); assert raises(lambda: fs.cd("nope")) and fs.pwd() == "/a/b"
    fs.touch("/a/f"); assert raises(lambda: fs.cd("../f")) and fs.pwd() == "/a/b"
    fs.cd("/"); fs.mkdir("/a//d/"); assert fs.ls("/a") == ["b", "c", "d", "f"]
    fs.cd("/a/./b/../b"); assert fs.pwd() == "/a/b"
    fs.cd("."); assert fs.pwd() == "/a/b"
    fs.write("x.txt", "rel"); assert fs.read("/a/b/x.txt") == "rel"
    assert fs.ls(".") == ["x.txt"] and fs.ls("..") == ["b", "c", "d", "f"]
    assert fs.run("cd ..") == "" and fs.run("pwd") == "/a"
    assert fs.run("ls b") == "x.txt"
    print("unix_filesystem reference OK")

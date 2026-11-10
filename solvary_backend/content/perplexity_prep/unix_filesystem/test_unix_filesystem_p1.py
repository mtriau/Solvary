# Part 1 provided tests: strict mkdir / touch / write / read / ls.
# Run with: pytest unix_filesystem -q
#
# Error contract: any error raises an OSError subclass or ValueError, so
# every raise check below accepts both. A failed operation must leave the
# file system unchanged; several tests assert state after the raise.

import pytest

from unix_filesystem import FileSystem

ERR = (OSError, ValueError)


def test_spec_example():
    fs = FileSystem()
    fs.mkdir("/a")
    fs.mkdir("/a/b")
    fs.write("/a/b/notes.txt", "hello")
    fs.write("/a/b/notes.txt", " world")
    fs.touch("/a/z.txt")
    assert fs.read("/a/b/notes.txt") == "hello world"
    assert fs.ls("/a") == ["b", "z.txt"]
    assert fs.ls("/a/b/notes.txt") == ["notes.txt"]
    assert fs.ls("/") == ["a"]


def test_ls_root_of_fresh_fs_is_empty_list():
    assert FileSystem().ls("/") == []


# ---------------------------------------------------------------- mkdir

def test_mkdir_is_strict_not_mkdir_p():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.mkdir("/x/y")
    assert fs.ls("/") == []


def test_mkdir_existing_dir_raises():
    fs = FileSystem()
    fs.mkdir("/a")
    with pytest.raises(ERR):
        fs.mkdir("/a")
    assert fs.ls("/") == ["a"]


def test_mkdir_over_existing_file_raises_and_keeps_file():
    fs = FileSystem()
    fs.write("/f", "data")
    with pytest.raises(ERR):
        fs.mkdir("/f")
    assert fs.read("/f") == "data"


def test_mkdir_root_raises():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.mkdir("/")
    assert fs.ls("/") == []


def test_mkdir_under_a_file_raises():
    fs = FileSystem()
    fs.touch("/a")
    with pytest.raises(ERR):
        fs.mkdir("/a/b")
    assert fs.ls("/a") == ["a"]


def test_mkdir_nested_when_parents_exist():
    fs = FileSystem()
    fs.mkdir("/a")
    fs.mkdir("/a/b")
    fs.mkdir("/a/b/c")
    assert fs.ls("/a/b") == ["c"]
    assert fs.ls("/a/b/c") == []


# ---------------------------------------------------------------- touch

def test_touch_creates_empty_file():
    fs = FileSystem()
    fs.touch("/f")
    assert fs.read("/f") == ""
    assert fs.ls("/") == ["f"]


def test_touch_existing_file_is_noop_and_preserves_content():
    fs = FileSystem()
    fs.write("/f", "keep me")
    fs.touch("/f")
    assert fs.read("/f") == "keep me"


def test_touch_existing_dir_raises():
    fs = FileSystem()
    fs.mkdir("/d")
    with pytest.raises(ERR):
        fs.touch("/d")
    assert fs.ls("/d") == []


def test_touch_root_raises():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.touch("/")
    assert fs.ls("/") == []


def test_touch_with_missing_parent_raises_and_creates_nothing():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.touch("/missing/f")
    assert fs.ls("/") == []


# ---------------------------------------------------------------- write

def test_write_creates_file_when_missing():
    fs = FileSystem()
    fs.mkdir("/a")
    fs.write("/a/f", "first")
    assert fs.read("/a/f") == "first"


def test_write_appends_not_overwrites():
    fs = FileSystem()
    fs.write("/f", "abc")
    fs.write("/f", "def")
    fs.write("/f", "")
    assert fs.read("/f") == "abcdef"


def test_write_to_directory_raises():
    fs = FileSystem()
    fs.mkdir("/a")
    with pytest.raises(ERR):
        fs.write("/a", "x")
    assert fs.ls("/a") == []


def test_write_with_missing_parent_raises_and_creates_nothing():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.write("/missing/f", "x")
    assert fs.ls("/") == []


# ---------------------------------------------------------------- read

def test_read_missing_file_raises():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.read("/nope")


def test_read_directory_raises():
    fs = FileSystem()
    fs.mkdir("/d")
    with pytest.raises(ERR):
        fs.read("/d")


# ---------------------------------------------------------------- ls

def test_ls_directory_returns_sorted_names():
    fs = FileSystem()
    fs.mkdir("/d")
    fs.touch("/d/zeta")
    fs.mkdir("/d/alpha")
    fs.touch("/d/mid")
    assert fs.ls("/d") == ["alpha", "mid", "zeta"]


def test_ls_file_returns_basename_not_full_path():
    fs = FileSystem()
    fs.mkdir("/a")
    fs.mkdir("/a/b")
    fs.touch("/a/b/f.txt")
    assert fs.ls("/a/b/f.txt") == ["f.txt"]


def test_ls_missing_path_raises():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.ls("/nope")


def test_descending_through_a_file_raises():
    fs = FileSystem()
    fs.touch("/f")
    with pytest.raises(ERR):
        fs.ls("/f/deeper")
    with pytest.raises(ERR):
        fs.read("/f/deeper")


def test_files_and_dirs_share_one_namespace():
    fs = FileSystem()
    fs.mkdir("/x")
    with pytest.raises(ERR):
        fs.touch("/x")
    fs.touch("/y")
    with pytest.raises(ERR):
        fs.mkdir("/y")
    assert fs.ls("/") == ["x", "y"]

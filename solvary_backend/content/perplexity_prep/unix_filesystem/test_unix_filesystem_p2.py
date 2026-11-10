# Part 2 provided tests: rm / rmdir / run(line).
# Run with: pytest unix_filesystem -q
#
# Error contract: any error raises an OSError subclass or ValueError. A
# failed operation leaves the file system unchanged.

import pytest

from unix_filesystem import FileSystem

ERR = (OSError, ValueError)


def make_fs() -> FileSystem:
    fs = FileSystem()
    fs.mkdir("/a")
    fs.mkdir("/a/empty")
    fs.write("/a/f", "data")
    return fs


# ---------------------------------------------------------------- rm

def test_rm_removes_a_file():
    fs = make_fs()
    fs.rm("/a/f")
    assert fs.ls("/a") == ["empty"]
    with pytest.raises(ERR):
        fs.read("/a/f")


def test_rm_missing_raises():
    fs = make_fs()
    with pytest.raises(ERR):
        fs.rm("/a/nope")
    assert fs.ls("/a") == ["empty", "f"]


def test_rm_directory_raises_and_keeps_it():
    fs = make_fs()
    with pytest.raises(ERR):
        fs.rm("/a/empty")
    assert fs.ls("/a") == ["empty", "f"]


def test_rm_then_recreate_starts_empty():
    fs = make_fs()
    fs.rm("/a/f")
    fs.touch("/a/f")
    assert fs.read("/a/f") == ""


# ---------------------------------------------------------------- rmdir

def test_rmdir_removes_empty_directory():
    fs = make_fs()
    fs.rmdir("/a/empty")
    assert fs.ls("/a") == ["f"]


def test_rmdir_non_empty_raises_and_leaves_it_intact():
    fs = make_fs()
    with pytest.raises(ERR):
        fs.rmdir("/a")
    assert fs.ls("/") == ["a"]
    assert fs.ls("/a") == ["empty", "f"]
    assert fs.read("/a/f") == "data"


def test_rmdir_missing_raises():
    fs = make_fs()
    with pytest.raises(ERR):
        fs.rmdir("/a/nope")


def test_rmdir_file_raises_and_keeps_file():
    fs = make_fs()
    with pytest.raises(ERR):
        fs.rmdir("/a/f")
    assert fs.read("/a/f") == "data"


def test_rmdir_root_raises():
    fs = make_fs()
    with pytest.raises(ERR):
        fs.rmdir("/")
    assert fs.ls("/") == ["a"]


def test_rmdir_after_emptying_succeeds():
    fs = make_fs()
    fs.rm("/a/f")
    fs.rmdir("/a/empty")
    fs.rmdir("/a")
    assert fs.ls("/") == []


# ---------------------------------------------------------------- run

def test_run_mkdir_touch_return_empty_string():
    fs = FileSystem()
    assert fs.run("mkdir /d") == ""
    assert fs.run("touch /d/f") == ""
    assert fs.ls("/d") == ["f"]


def test_run_write_then_read_returns_content():
    fs = FileSystem()
    assert fs.run("write /f hello") == ""
    assert fs.run("read /f") == "hello"


def test_write_command_preserves_inner_spaces():
    fs = FileSystem()
    fs.run("write /f hello   world")
    assert fs.run("read /f") == "hello   world"


def test_write_command_preserves_trailing_space():
    fs = FileSystem()
    fs.run("write /f tail ")
    assert fs.run("read /f") == "tail "


def test_write_command_appends_across_calls():
    fs = FileSystem()
    fs.run("write /f ab")
    fs.run("write /f cd")
    assert fs.run("read /f") == "abcd"


def test_write_command_with_no_content_creates_empty_file():
    fs = FileSystem()
    assert fs.run("write /f") == ""
    assert fs.run("read /f") == ""
    assert fs.ls("/") == ["f"]


def test_ls_command_joins_sorted_names_with_single_space():
    fs = FileSystem()
    fs.run("mkdir /d")
    fs.run("touch /d/zeta")
    fs.run("mkdir /d/alpha")
    fs.run("touch /d/mid")
    assert fs.run("ls /d") == "alpha mid zeta"


def test_ls_command_on_empty_root_returns_empty_string():
    assert FileSystem().run("ls /") == ""


def test_ls_command_on_file_returns_basename():
    fs = FileSystem()
    fs.run("mkdir /d")
    fs.run("touch /d/f.txt")
    assert fs.run("ls /d/f.txt") == "f.txt"


def test_rm_and_rmdir_commands_return_empty_string():
    fs = make_fs()
    assert fs.run("rm /a/f") == ""
    assert fs.run("rmdir /a/empty") == ""
    assert fs.run("ls /a") == ""


def test_run_unknown_command_raises_value_error():
    fs = FileSystem()
    with pytest.raises(ValueError):
        fs.run("frobnicate /a")
    assert fs.ls("/") == []


def test_run_propagates_underlying_errors():
    fs = FileSystem()
    with pytest.raises(ERR):
        fs.run("read /nope")
    with pytest.raises(ERR):
        fs.run("mkdir /x/y")
    with pytest.raises(ERR):
        fs.run("rmdir /")
    assert fs.ls("/") == []


def test_run_matches_direct_method_calls():
    via_run, direct = FileSystem(), FileSystem()
    via_run.run("mkdir /a")
    via_run.run("write /a/f one two")
    via_run.run("touch /a/g")
    direct.mkdir("/a")
    direct.write("/a/f", "one two")
    direct.touch("/a/g")
    assert via_run.ls("/a") == direct.ls("/a")
    assert via_run.read("/a/f") == direct.read("/a/f")

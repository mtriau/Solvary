# Part 3 provided tests: cd / pwd / relative paths.
# Run with: pytest unix_filesystem -q
#
# Error contract: any error raises an OSError subclass or ValueError. A
# failed operation leaves the file system (and the cwd) unchanged.

import pytest

from unix_filesystem import FileSystem

ERR = (OSError, ValueError)


def make_fs() -> FileSystem:
    fs = FileSystem()
    fs.mkdir("/a")
    fs.mkdir("/a/b")
    fs.mkdir("/shared")
    fs.write("/shared/s.txt", "shared")
    fs.write("/a/f.txt", "file")
    return fs


# ---------------------------------------------------------------- cd / pwd

def test_pwd_starts_at_root():
    assert FileSystem().pwd() == "/"


def test_cd_absolute_then_pwd_has_no_trailing_slash():
    fs = make_fs()
    fs.cd("/a/b")
    assert fs.pwd() == "/a/b"


def test_cd_relative_child():
    fs = make_fs()
    fs.cd("a")
    fs.cd("b")
    assert fs.pwd() == "/a/b"


def test_cd_dotdot_goes_up():
    fs = make_fs()
    fs.cd("/a/b")
    fs.cd("..")
    assert fs.pwd() == "/a"


def test_cd_dotdot_past_root_stays_at_root():
    fs = make_fs()
    fs.cd("/a/b")
    fs.cd("../../..")
    assert fs.pwd() == "/"


def test_cd_dot_is_noop():
    fs = make_fs()
    fs.cd("/a/b")
    fs.cd(".")
    assert fs.pwd() == "/a/b"


def test_cd_with_dot_and_dotdot_segments_normalizes():
    fs = make_fs()
    fs.cd("/a/./b/../b")
    assert fs.pwd() == "/a/b"


def test_cd_to_missing_dir_leaves_cwd_unchanged():
    fs = make_fs()
    fs.cd("/a/b")
    with pytest.raises(ERR):
        fs.cd("nope")
    assert fs.pwd() == "/a/b"


def test_cd_to_file_raises_and_leaves_cwd_unchanged():
    fs = make_fs()
    fs.cd("/a/b")
    with pytest.raises(ERR):
        fs.cd("../f.txt")
    assert fs.pwd() == "/a/b"


def test_cd_tolerates_trailing_slash():
    fs = make_fs()
    fs.cd("/a/")
    assert fs.pwd() == "/a"
    fs.cd("b/")
    assert fs.pwd() == "/a/b"


# ---------------------------------------------------------------- relative paths in other ops

def test_mkdir_relative_dotdot_creates_sibling():
    fs = make_fs()
    fs.cd("/a/b")
    fs.mkdir("../c")
    assert fs.ls("/a") == ["b", "c", "f.txt"]


def test_mkdir_tolerates_repeated_and_trailing_slashes():
    fs = FileSystem()
    fs.mkdir("/a")
    fs.mkdir("/a//b/")
    assert fs.ls("/a") == ["b"]


def test_write_and_read_relative_paths():
    fs = make_fs()
    fs.cd("/a/b")
    fs.write("notes.txt", "rel")
    assert fs.read("./notes.txt") == "rel"
    assert fs.read("/a/b/notes.txt") == "rel"
    assert fs.read("../../shared/s.txt") == "shared"


def test_touch_relative_then_ls_dot():
    fs = make_fs()
    fs.cd("/a/b")
    fs.touch("x")
    assert fs.ls(".") == ["x"]
    assert fs.ls("..") == ["b", "f.txt"]


def test_ls_relative_file_returns_basename():
    fs = make_fs()
    fs.cd("/a")
    assert fs.ls("f.txt") == ["f.txt"]
    assert fs.ls("../shared/s.txt") == ["s.txt"]


def test_rm_and_rmdir_relative_paths():
    fs = make_fs()
    fs.cd("/a")
    fs.rm("f.txt")
    fs.rmdir("./b")
    assert fs.ls(".") == []
    assert fs.ls("/a") == []


def test_absolute_paths_ignore_cwd():
    fs = make_fs()
    fs.cd("/a/b")
    fs.mkdir("/top")
    assert fs.ls("/") == ["a", "shared", "top"]
    assert fs.ls("/a/b") == []


def test_relative_op_with_missing_parent_raises_and_creates_nothing():
    fs = make_fs()
    fs.cd("/a")
    with pytest.raises(ERR):
        fs.mkdir("nope/deeper")
    with pytest.raises(ERR):
        fs.write("nope/f", "x")
    assert fs.ls(".") == ["b", "f.txt"]


# ---------------------------------------------------------------- run with cd / pwd

def test_run_cd_returns_empty_and_pwd_returns_path():
    fs = make_fs()
    assert fs.run("cd /a/b") == ""
    assert fs.run("pwd") == "/a/b"
    assert fs.run("cd ..") == ""
    assert fs.run("pwd") == "/a"


def test_run_pwd_at_root():
    assert FileSystem().run("pwd") == "/"


def test_run_commands_accept_relative_paths():
    fs = make_fs()
    fs.run("cd /a")
    assert fs.run("mkdir c") == ""
    assert fs.run("write c/f.txt hi there") == ""
    assert fs.run("read c/f.txt") == "hi there"
    assert fs.run("ls .") == "b c f.txt"
    assert fs.run("ls ../shared") == "s.txt"


def test_run_cd_to_missing_raises_and_leaves_cwd_unchanged():
    fs = make_fs()
    fs.run("cd /a")
    with pytest.raises(ERR):
        fs.run("cd nope")
    assert fs.run("pwd") == "/a"

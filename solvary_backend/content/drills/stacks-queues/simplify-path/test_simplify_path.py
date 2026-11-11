from simplify_path import simplify_path


def test_example():
    assert simplify_path("/a/./b/../../c/") == "/c"


def test_parent_of_root_is_root():
    assert simplify_path("/../") == "/"


def test_repeated_slashes_and_trailing_slash():
    assert simplify_path("/home//foo/") == "/home/foo"


def test_root():
    assert simplify_path("/") == "/"


def test_dot_dot_dot_is_a_name():
    assert simplify_path("/a/.../b") == "/a/.../b"


def test_many_parents():
    assert simplify_path("/a/b/c/../../..") == "/"

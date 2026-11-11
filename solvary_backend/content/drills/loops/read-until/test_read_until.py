from read_until import read_until


def _reader(lines):
    it = iter(lines)
    return lambda: next(it)


def test_example():
    assert read_until(_reader(["a", "b", "", "c"]), "") == ["a", "b"]


def test_sentinel_first():
    assert read_until(_reader(["END", "x"]), "END") == []


def test_does_not_read_past_the_sentinel():
    calls = []

    def read():
        calls.append(1)
        if len(calls) > 3:
            raise AssertionError("read() called after the sentinel")
        return ["x", "y", "STOP"][len(calls) - 1]

    assert read_until(read, "STOP") == ["x", "y"]
    assert len(calls) == 3


def test_sentinel_compared_by_equality_not_identity():
    assert read_until(_reader(["a", "".join(["e", "nd"]), "b"]), "end") == ["a"]


def test_only_the_exact_sentinel_stops_the_loop():
    assert read_until(_reader(["", " ", "EOF", "x"]), "EOF") == ["", " "]


def test_many_lines():
    lines = [str(i) for i in range(10_000)] + ["", "tail"]
    assert read_until(_reader(lines), "") == [str(i) for i in range(10_000)]

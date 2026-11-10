from first_negative import first_negative


def test_example():
    assert first_negative([3, -1, -5]) == -1


def test_none_when_absent():
    assert first_negative([1, 2]) is None


def test_empty():
    assert first_negative([]) is None


def test_zero_is_not_negative():
    assert first_negative([0, -0, -3]) == -3


def test_stops_at_the_first_match():
    def numbers():
        yield 4
        yield -2
        raise AssertionError("consumed past the first negative")

    assert first_negative(numbers()) == -2

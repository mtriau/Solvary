from all_and_any import all_passed, any_failed


def test_all_passed():
    assert all_passed([70, 85], 60) is True
    assert all_passed([70, 55], 60) is False


def test_any_failed():
    assert any_failed([70, 55], 60) is True
    assert any_failed([70, 85], 60) is False


def test_empty_is_vacuous():
    assert all_passed([], 60) is True
    assert any_failed([], 60) is False


def test_threshold_is_inclusive():
    assert all_passed([60], 60) is True
    assert any_failed([60], 60) is False


def test_short_circuits():
    def scores():
        yield 10
        raise AssertionError("kept reading after the answer was known")

    assert all_passed(scores(), 60) is False
    assert any_failed(scores(), 60) is True

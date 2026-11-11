from moving_averages import moving_averages


def test_example():
    assert moving_averages([1, 2, 3, 4], 2) == [1.0, 1.5, 2.5, 3.5]


def test_window_larger_than_input():
    assert moving_averages([10, 20, 30], 5) == [10.0, 15.0, 20.0]


def test_empty():
    assert moving_averages([], 3) == []


def test_window_of_one_echoes_input():
    assert moving_averages([3, 9, 27], 1) == [3.0, 9.0, 27.0]


def test_oldest_value_drops_out():
    assert moving_averages([100, 0, 0, 0], 2) == [100.0, 50.0, 0.0, 0.0]


def test_accepts_an_iterator():
    assert moving_averages(iter([2, 4]), 2) == [2.0, 3.0]

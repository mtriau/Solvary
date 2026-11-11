from climb_stairs import climb


def test_base_cases():
    assert climb(0) == 1
    assert climb(1) == 1


def test_two_steps():
    assert climb(2) == 2


def test_five_steps():
    assert climb(5) == 8


def test_ten_steps():
    assert climb(10) == 89


def test_large_n_needs_memoisation():
    assert climb(500) == int(
        "2255915161619363308725126950360720720460113249137581905886388664184746"
        "27738686883405015987052796968498626"
    )


def test_repeated_calls_are_consistent():
    assert climb(30) == climb(30) == 1346269

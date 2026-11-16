# Provided tests for Part 3: Match and play().

import pytest
import tennis_scoring as ts


def feed(obj, points):
    for ch in points:
        obj.record_point(ch)
    return obj


def games(p, n=1):
    return p * 4 * n


def set_for(p):
    """Points for a 6-0 set won by p."""
    return games(p, 6)


def test_new_match_state():
    m = ts.Match()
    assert m.score() == "0-0 sets, 0-0, 0-0"
    assert m.sets() == [(0, 0)]
    assert m.winner() is None


def test_score_format_while_in_progress():
    m = feed(ts.Match(), set_for("A") + games("A", 4) + games("B", 3) + "AAB")
    assert m.score() == "1-0 sets, 4-3, 30-15"


def test_sets_lists_finished_sets_then_current_games():
    m = feed(ts.Match(), set_for("A") + games("B", 2) + games("A"))
    assert m.sets() == [(6, 0), (1, 2)]
    feed(m, games("B", 4))
    assert m.score() == "1-1 sets, 0-0, 0-0"
    assert m.sets() == [(6, 0), (1, 6), (0, 0)]


def test_match_won_in_straight_sets():
    m = feed(ts.Match(), set_for("A") + set_for("A"))
    assert m.winner() == "A"
    assert m.score() == "match A"
    assert m.sets() == [(6, 0), (6, 0)]


def test_match_goes_to_three_sets():
    m = feed(ts.Match(), set_for("A") + set_for("B"))
    assert m.winner() is None
    assert m.score() == "1-1 sets, 0-0, 0-0"
    feed(m, set_for("B"))
    assert m.winner() == "B"
    assert m.score() == "match B"
    assert m.sets() == [(6, 0), (0, 6), (0, 6)]


def test_tiebreak_set_inside_a_match():
    m = feed(ts.Match(), games("A", 5) + games("B", 5) + games("A") + games("B"))
    assert m.score() == "0-0 sets, 6-6, 0-0"
    feed(m, "AAAAAAA")
    assert m.sets() == [(7, 6), (0, 0)]
    assert m.score() == "1-0 sets, 0-0, 0-0"


def test_best_of_five_needs_three_sets():
    m = ts.Match(best_of=5)
    feed(m, set_for("A") + set_for("A"))
    assert m.winner() is None
    assert m.score() == "2-0 sets, 0-0, 0-0"
    feed(m, set_for("B") + set_for("B"))
    assert m.winner() is None
    assert m.score() == "2-2 sets, 0-0, 0-0"
    feed(m, set_for("A"))
    assert m.winner() == "A"
    assert m.score() == "match A"
    assert len(m.sets()) == 5


def test_best_of_must_be_three_or_five():
    for bad in (0, 1, 2, 4, 7, -3):
        with pytest.raises(ValueError):
            ts.Match(best_of=bad)
    assert ts.Match(3).winner() is None
    assert ts.Match(5).winner() is None


def test_points_after_match_raise():
    m = feed(ts.Match(), set_for("A") + set_for("A"))
    with pytest.raises(ValueError):
        m.record_point("B")
    assert m.score() == "match A"


def test_play_returns_a_score_after_every_point():
    assert ts.play("AAB") == [
        "0-0 sets, 0-0, 15-0",
        "0-0 sets, 0-0, 30-0",
        "0-0 sets, 0-0, 30-15",
    ]


def test_play_full_straight_sets_match():
    out = ts.play("A" * 48)
    assert len(out) == 48
    assert out[3] == "0-0 sets, 1-0, 0-0"
    assert out[23] == "1-0 sets, 0-0, 0-0"
    assert out[-1] == "match A"
    assert out[-2].startswith("1-0 sets, 5-0, ")


def test_play_invalid_character_raises():
    for bad in ("AAX", "a", "A B", "AB1"):
        with pytest.raises(ValueError):
            ts.play(bad)


def test_play_point_after_match_end_raises():
    with pytest.raises(ValueError):
        ts.play("A" * 49)

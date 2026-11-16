# Provided tests for Part 2: Set and the tiebreak.

import pytest
import tennis_scoring as ts


def feed(obj, points):
    for ch in points:
        obj.record_point(ch)
    return obj


def games(p, n=1):
    """Points for n love games won by p."""
    return p * 4 * n


def set_at(a, b):
    """A set where A has won `a` games and B `b` (alternating while both can)."""
    s = ts.Set()
    for _ in range(min(a, b)):
        feed(s, games("A") + games("B"))
    feed(s, games("A", a - min(a, b)))
    feed(s, games("B", b - min(a, b)))
    return s


def test_new_set_score_and_state():
    s = ts.Set()
    assert s.games() == (0, 0)
    assert s.score() == "0-0, 0-0"
    assert s.winner() is None
    assert s.in_tiebreak() is False


def test_score_shows_games_then_current_game():
    s = feed(set_at(4, 3), "AAB")
    assert s.games() == (4, 3)
    assert s.score() == "4-3, 30-15"


def test_new_game_starts_automatically_after_a_game():
    s = feed(ts.Set(), "AAAA")
    assert s.games() == (1, 0)
    assert s.score() == "1-0, 0-0"
    s.record_point("B")
    assert s.score() == "1-0, 0-15"


def test_game_uses_deuce_rules_inside_the_set():
    s = feed(ts.Set(), "ABABAB")
    assert s.score() == "0-0, deuce"
    s.record_point("B")
    assert s.score() == "0-0, advantage B"
    s.record_point("B")
    assert s.games() == (0, 1)


def test_six_love_wins_the_set():
    s = feed(ts.Set(), games("A", 6))
    assert s.winner() == "A"
    assert s.score() == "set A"
    assert s.games() == (6, 0)


def test_six_five_is_not_a_set():
    s = set_at(6, 5)
    assert s.winner() is None
    assert s.in_tiebreak() is False
    assert s.score() == "6-5, 0-0"


def test_seven_five_wins_the_set():
    s = feed(set_at(6, 5), games("A"))
    assert s.games() == (7, 5)
    assert s.winner() == "A"
    assert s.score() == "set A"


def test_six_five_then_other_player_levels_into_tiebreak():
    s = feed(set_at(6, 5), games("B"))
    assert s.games() == (6, 6)
    assert s.in_tiebreak() is True


def test_tiebreak_scores_in_raw_points():
    s = set_at(6, 6)
    assert s.in_tiebreak() is True
    assert s.score() == "6-6, 0-0"
    feed(s, "AAB")
    assert s.score() == "6-6, 2-1"


def test_tiebreak_to_seven_ends_the_set_seven_six():
    s = feed(set_at(6, 6), "AAAAAAA")
    assert s.winner() == "A"
    assert s.games() == (7, 6)
    assert s.score() == "set A"
    assert s.in_tiebreak() is False


def test_tiebreak_must_be_won_by_two():
    s = set_at(6, 6)
    feed(s, "AAAAAA" + "BBBBBB")  # 6-6 in points
    assert s.winner() is None
    feed(s, "A")
    assert s.winner() is None
    assert s.score() == "6-6, 7-6"
    feed(s, "BB")
    assert s.winner() is None
    assert s.score() == "6-6, 7-8"
    feed(s, "B")
    assert s.winner() == "B"
    assert s.games() == (6, 7)


def test_point_after_set_won_raises():
    s = feed(ts.Set(), games("A", 6))
    with pytest.raises(ValueError):
        s.record_point("A")
    assert s.games() == (6, 0)


def test_unknown_player_raises_in_set():
    s = ts.Set()
    with pytest.raises(ValueError):
        s.record_point("X")
    assert s.score() == "0-0, 0-0"

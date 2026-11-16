# Provided tests for Part 1: Game.

import pytest
import tennis_scoring as ts


def feed(game, points):
    for ch in points:
        game.record_point(ch)
    return game


def test_new_game_is_love_all():
    g = ts.Game()
    assert g.score() == "0-0"
    assert g.points() == (0, 0)
    assert g.winner() is None


def test_call_progression_for_one_player():
    g = ts.Game()
    seen = []
    for _ in range(3):
        g.record_point("A")
        seen.append(g.score())
    assert seen == ["15-0", "30-0", "40-0"]


def test_scores_read_a_first_for_both_players():
    g = feed(ts.Game(), "AB")
    assert g.score() == "15-15"
    g.record_point("A")
    assert g.score() == "30-15"
    g.record_point("B")
    g.record_point("B")
    assert g.score() == "30-40"


def test_game_won_four_nil():
    g = feed(ts.Game(), "AAAA")
    assert g.winner() == "A"
    assert g.score() == "game A"
    assert g.points() == (4, 0)


def test_game_not_over_at_two_nil():
    g = feed(ts.Game(), "AA")
    assert g.winner() is None


def test_game_won_four_two():
    g = feed(ts.Game(), "ABABAA")
    assert g.winner() == "A"
    assert g.score() == "game A"


def test_game_can_be_won_by_b():
    g = feed(ts.Game(), "BBBAB")
    assert g.winner() == "B"
    assert g.score() == "game B"
    assert g.points() == (1, 4)


def test_forty_thirty_then_leader_scores_wins():
    g = feed(ts.Game(), "AAABB")
    assert g.score() == "40-30"
    g.record_point("A")
    assert g.winner() == "A"


def test_three_all_is_deuce_first_time():
    g = feed(ts.Game(), "ABABAB")
    assert g.score() == "deuce"
    assert g.winner() is None


def test_advantage_then_win():
    g = feed(ts.Game(), "ABABABA")
    assert g.score() == "advantage A"
    g.record_point("A")
    assert g.score() == "game A"
    assert g.winner() == "A"


def test_advantage_lost_returns_to_deuce():
    g = feed(ts.Game(), "ABABABB")
    assert g.score() == "advantage B"
    g.record_point("A")
    assert g.score() == "deuce"
    g.record_point("A")
    assert g.score() == "advantage A"


def test_long_deuce_marathon_is_decided_correctly():
    g = feed(ts.Game(), "ABABAB")
    for _ in range(20):
        g.record_point("A")
        assert g.score() == "advantage A"
        g.record_point("B")
        assert g.score() == "deuce"
    g.record_point("B")
    assert g.score() == "advantage B"
    g.record_point("B")
    assert g.winner() == "B"
    assert g.points() == (23, 25)


def test_point_after_game_is_decided_raises_and_changes_nothing():
    g = feed(ts.Game(), "AAAA")
    with pytest.raises(ValueError):
        g.record_point("B")
    assert g.points() == (4, 0)
    assert g.score() == "game A"


def test_unknown_player_raises_and_changes_nothing():
    g = feed(ts.Game(), "A")
    for bad in ("C", "a", "", "AB"):
        with pytest.raises(ValueError):
            g.record_point(bad)
    assert g.points() == (1, 0)

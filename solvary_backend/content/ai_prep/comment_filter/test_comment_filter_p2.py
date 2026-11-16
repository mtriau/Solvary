# Provided tests for Part 2: score-based retention (plus the Part 1 suite).

import time

import comment_filter as cf
import pytest


def cat(id, parent=None, points=0):
    return {"id": id, "parent": parent, "cat": True, "dog": False, "points": points}


def dog(id, parent=None, points=0):
    return {"id": id, "parent": parent, "cat": False, "dog": True, "points": points}


def spec_forest():
    return [
        cat(10, None, 1),
        dog(11, 10, 5),
        cat(12, 11, 50),
        dog(13, 11, -3),
        dog(14, 10, 2),
        dog(15, None, -30),
        dog(16, 15, 30),
        cat(17, 15, 1),
    ]


def test_spec_example_with_and_without_threshold():
    comments = spec_forest()
    assert cf.comments_to_exclude(comments, "cat", threshold=10) == [13, 14, 15, 17]
    assert cf.visible_comments(comments, "cat", threshold=10) == [10, 11, 12, 16]
    assert cf.comments_to_exclude(comments, "cat") == [11, 12, 13, 14, 15, 16, 17]


def test_qualifying_hidden_subtree_is_kept_with_its_descendants():
    comments = [dog(1, None, 6), cat(2, 1, 5)]
    assert cf.comments_to_exclude(comments, "cat", threshold=10) == []
    assert cf.comments_to_exclude(comments, "cat", threshold=11) == [1, 2]


def test_total_equal_to_threshold_does_not_qualify():
    comments = [dog(1, None, 6), cat(2, 1, 4)]
    assert cf.comments_to_exclude(comments, "cat", threshold=10) == [1, 2]
    assert cf.comments_to_exclude(comments, "cat", threshold=9) == []


def test_hidden_descendants_points_count_towards_the_total():
    comments = [dog(1, None, 3), dog(2, 1, 20)]
    # 2 qualifies on its own (20 > 15) and 1 qualifies through it (23 > 15).
    assert cf.comments_to_exclude(comments, "cat", threshold=15) == []
    # 1 qualifies (23 > 21) but 2 does not (20 <= 21): the nearest hidden rule.
    assert cf.comments_to_exclude(comments, "cat", threshold=21) == [2]


def test_qualifying_subtree_nested_in_a_non_qualifying_hidden_one_is_kept():
    comments = [dog(1, None, -30), dog(2, 1, 50), cat(3, 2, 0), cat(4, 1, 1)]
    # totals: 1 -> 21, 2 -> 50, so only 2 qualifies at threshold 30.
    assert cf.subtree_points(comments)[1] == 21
    assert cf.comments_to_exclude(comments, "cat", threshold=30) == [1, 4]
    assert cf.visible_comments(comments, "cat", threshold=30) == [2, 3]


def test_non_qualifying_hidden_comment_inside_a_qualifying_one_is_excluded():
    comments = [dog(1, None, 50), dog(2, 1, -5), cat(3, 2, 1), cat(4, 1, 2)]
    # totals: 1 -> 48, 2 -> -4. At threshold 40 only 1 qualifies.
    assert cf.comments_to_exclude(comments, "cat", threshold=40) == [2, 3]


def test_visible_comment_inherits_from_the_nearest_hidden_ancestor():
    comments = [dog(1, None, 100), cat(2, 1, 0), dog(3, 2, -100), cat(4, 3, 500)]
    # 1 qualifies, 2 is fine under it, 3 is hidden and total 400 qualifies,
    # so 4 stays too. Raise the threshold and 3 stops qualifying.
    assert cf.comments_to_exclude(comments, "cat", threshold=50) == []
    assert cf.comments_to_exclude(comments, "cat", threshold=450) == [3, 4]


def test_negative_points_and_negative_thresholds():
    comments = [dog(1, None, 20), cat(2, 1, -15)]
    assert cf.comments_to_exclude(comments, "cat", threshold=4) == []
    assert cf.comments_to_exclude(comments, "cat", threshold=5) == [1, 2]
    losing = [dog(1, None, -1), cat(2, 1, -2)]
    assert cf.comments_to_exclude(losing, "cat", threshold=-5) == []
    assert cf.comments_to_exclude(losing, "cat", threshold=-3) == [1, 2]


def test_threshold_none_matches_part_one_whatever_the_points():
    comments = spec_forest()
    with_none = cf.comments_to_exclude(comments, "cat", threshold=None)
    assert with_none == cf.comments_to_exclude(comments, "cat")
    assert cf.visible_comments(comments, "cat") == [10]
    rich = [dog(1, None, 10**6), cat(2, 1, 10**6)]
    assert cf.comments_to_exclude(rich, "cat") == [1, 2]
    assert cf.comments_to_exclude(rich, "cat", None) == [1, 2]


def test_threshold_works_in_dog_mode_and_with_children_before_parents():
    comments = [cat(4, 3, 1), cat(3, 2, 200), dog(2, 1, 0), dog(1, None, 0)]
    # Dog viewer: 3 and 4 are cats, hidden. 3 totals 201, 4 totals 1.
    assert cf.comments_to_exclude(comments, "dog", threshold=100) == [4]
    assert cf.visible_comments(comments, "dog", threshold=100) == [3, 2, 1]
    assert cf.comments_to_exclude(comments, "dog", threshold=300) == [4, 3]


def test_subtree_points_ignores_input_order_and_validates_parents():
    comments = [cat(3, 2, 4), cat(2, 1, 2), cat(1, None, 1), cat(9, None, -5)]
    assert cf.subtree_points(comments) == {1: 7, 2: 6, 3: 4, 9: -5}
    with pytest.raises(ValueError):
        cf.subtree_points([cat(1, 7, 1)])


def test_deep_chain_of_200k_with_scores_is_linear():
    n = 200_000
    comments = [cat(i, i - 1, 1) for i in range(n - 1, 0, -1)]
    comments.append(dog(0, None, 1))
    start = time.perf_counter()
    totals = cf.subtree_points(comments)
    kept = cf.comments_to_exclude(comments, "cat", threshold=100)
    dropped = cf.comments_to_exclude(comments, "cat", threshold=10**9)
    elapsed = time.perf_counter() - start
    assert totals[0] == n and totals[n - 1] == 1
    assert kept == []
    assert len(dropped) == n
    assert elapsed < 2.0

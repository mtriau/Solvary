# Provided tests for Part 3: visible thread order (plus Parts 1 and 2).

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


def test_spec_example_reparents_a_kept_comment_to_top_level():
    assert cf.render_thread(spec_forest(), "cat", threshold=10) == [
        (0, 16),
        (0, 10),
        (1, 11),
        (2, 12),
    ]


def test_top_level_sorted_by_points_descending_then_id():
    comments = [cat(3, None, 5), cat(1, None, 5), cat(2, None, 9), cat(4, None, -1)]
    assert cf.render_thread(comments, "cat") == [(0, 2), (0, 1), (0, 3), (0, 4)]


def test_children_follow_their_parent_depth_first_with_the_same_ordering():
    comments = [
        cat(1, None, 0),
        cat(2, 1, 3),
        cat(3, 1, 7),
        cat(4, 2, 0),
        cat(5, 3, 0),
        cat(6, None, -1),
    ]
    assert cf.render_thread(comments, "cat") == [
        (0, 1),
        (1, 3),
        (2, 5),
        (1, 2),
        (2, 4),
        (0, 6),
    ]


def test_equal_points_break_ties_by_id_at_every_level():
    comments = [cat(1), cat(9, 1, 2), cat(4, 1, 2), cat(7, 4, 0), cat(6, 4, 0)]
    assert cf.render_thread(comments, "cat") == [
        (0, 1),
        (1, 4),
        (2, 6),
        (2, 7),
        (1, 9),
    ]


def test_excluded_comments_and_their_subtrees_are_absent():
    comments = [cat(1), dog(2, 1), cat(3, 2), cat(4, 1)]
    assert cf.render_thread(comments, "cat") == [(0, 1), (1, 4)]
    assert cf.render_thread(comments, "dog") == []


def test_kept_comment_under_excluded_parent_attaches_to_nearest_visible_ancestor():
    comments = [cat(1, None, 0), dog(2, 1, -90), dog(3, 2, 100), cat(4, 3, 1)]
    # 2 totals 11 (excluded at 20); 3 totals 101 (kept); 4 stays under 3.
    assert cf.render_thread(comments, "cat", threshold=20) == [(0, 1), (1, 3), (2, 4)]


def test_kept_comment_with_no_visible_ancestor_becomes_top_level():
    comments = [dog(1, None, -90), dog(2, 1, 100), cat(3, 2, 1)]
    assert cf.render_thread(comments, "cat", threshold=20) == [(0, 2), (1, 3)]


def test_reparented_comment_sorts_among_its_new_siblings():
    comments = [
        cat(1, None, 0),
        cat(2, 1, 5),
        dog(3, 1, -90),
        dog(4, 3, 100),
        cat(5, 4, 1),
    ]
    # 3 totals 11 and is excluded; 4 totals 101 and is kept, so it becomes a
    # child of 1 and, with 100 points, comes before comment 2.
    assert cf.render_thread(comments, "cat", threshold=20) == [
        (0, 1),
        (1, 4),
        (2, 5),
        (1, 2),
    ]


def test_several_excluded_levels_are_skipped_and_equal_total_is_excluded():
    comments = [
        cat(1, None, 0),
        dog(2, 1, -100),
        dog(3, 2, -100),
        dog(4, 3, 500),
        cat(5, 4, 0),
    ]
    # totals: 2 -> 300, 3 -> 400 (equals the threshold, so it does not
    # qualify), 4 -> 500. Only 4 is kept and it hangs from comment 1.
    assert cf.render_thread(comments, "cat", threshold=400) == [(0, 1), (1, 4), (2, 5)]


def test_render_matches_visible_comments_and_ignores_input_order():
    comments = spec_forest()
    forward = cf.render_thread(comments, "cat", threshold=10)
    backward = cf.render_thread(comments[::-1], "cat", threshold=10)
    assert forward == backward
    visible = cf.visible_comments(comments, "cat", threshold=10)
    assert sorted(i for _, i in forward) == sorted(visible)


def test_errors_are_the_same_as_before():
    with pytest.raises(ValueError):
        cf.render_thread([cat(1)], "bird")
    with pytest.raises(ValueError):
        cf.render_thread([cat(1), cat(2, 8)], "cat", threshold=3)


def test_deep_chain_of_200k_renders_without_recursion():
    n = 200_000
    comments = [cat(i, i - 1, 0) for i in range(n - 1, 0, -1)]
    comments.append(cat(0, None, 0))
    start = time.perf_counter()
    thread = cf.render_thread(comments, "cat")
    elapsed = time.perf_counter() - start
    assert len(thread) == n
    assert thread[0] == (0, 0) and thread[-1] == (n - 1, n - 1)
    assert elapsed < 2.0

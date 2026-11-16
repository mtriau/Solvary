# Provided tests for Part 1: exclude a category and its subtrees.

import time

import comment_filter as cf
import pytest


def c(id, parent=None, cat=True, dog=False, points=0):
    return {"id": id, "parent": parent, "cat": cat, "dog": dog, "points": points}


def spec_forest():
    return [
        c(1, None, cat=True),
        c(2, 1, cat=False, dog=True),
        c(3, 2, cat=True),
        c(4, 1, cat=True),
        c(5, None, cat=False, dog=True),
        c(6, 5, cat=True),
        c(7, 6, cat=True),
        c(8, 7, cat=True),
    ]


def test_spec_example_cat_viewer():
    comments = spec_forest()
    assert cf.comments_to_exclude(comments, "cat") == [2, 3, 5, 6, 7, 8]
    assert cf.visible_comments(comments, "cat") == [1, 4]


def test_spec_example_dog_viewer():
    comments = spec_forest()
    assert cf.visible_comments(comments, "dog") == [5]
    assert cf.comments_to_exclude(comments, "dog") == [1, 2, 3, 4, 6, 7, 8]


def test_whole_chain_under_a_hidden_root_is_excluded():
    comments = [c(5, None, cat=False, dog=True), c(6, 5), c(7, 6), c(8, 7)]
    assert cf.comments_to_exclude(comments, "cat") == [5, 6, 7, 8]
    assert cf.visible_comments(comments, "cat") == []


def test_cat_descendant_of_a_dog_comment_is_excluded():
    comments = [c(1), c(2, 1, cat=False, dog=True), c(3, 2, cat=True)]
    assert cf.comments_to_exclude(comments, "cat") == [2, 3]


def test_only_the_viewers_flag_matters():
    comments = [c(1, cat=True, dog=True), c(2, cat=False, dog=False)]
    assert cf.visible_comments(comments, "cat") == [1]
    assert cf.visible_comments(comments, "dog") == [1]
    assert cf.comments_to_exclude(comments, "cat") == [2]
    assert cf.comments_to_exclude(comments, "dog") == [2]


def test_output_follows_input_order_not_id_or_tree_order():
    comments = [
        c(30, None, cat=False),
        c(10, None),
        c(20, 30),
        c(40, 10, cat=False),
        c(5, 40),
    ]
    assert cf.comments_to_exclude(comments, "cat") == [30, 20, 40, 5]
    assert cf.visible_comments(comments, "cat") == [10]


def test_children_may_come_before_their_parents():
    comments = [c(8, 7), c(7, 6), c(6, 5), c(5, None, cat=False), c(1)]
    assert cf.comments_to_exclude(comments, "cat") == [8, 7, 6, 5]
    assert cf.visible_comments(comments, "cat") == [1]


def test_visible_is_the_complement_of_excluded():
    comments = spec_forest()
    for mode in ("cat", "dog"):
        gone = set(cf.comments_to_exclude(comments, mode))
        kept = cf.visible_comments(comments, mode)
        assert gone.isdisjoint(kept)
        assert sorted(gone | set(kept)) == sorted(x["id"] for x in comments)


def test_empty_input_and_input_is_not_modified():
    assert cf.comments_to_exclude([], "cat") == []
    assert cf.visible_comments([], "dog") == []
    comments = spec_forest()
    snapshot = [dict(x) for x in comments]
    cf.comments_to_exclude(comments, "cat")
    cf.visible_comments(comments, "dog")
    assert comments == snapshot


def test_missing_parent_raises_value_error():
    comments = [c(1), c(2, 99)]
    with pytest.raises(ValueError):
        cf.comments_to_exclude(comments, "cat")
    with pytest.raises(ValueError):
        cf.visible_comments(comments, "cat")


def test_unknown_mode_raises_value_error():
    with pytest.raises(ValueError):
        cf.comments_to_exclude([c(1)], "bird")
    with pytest.raises(ValueError):
        cf.visible_comments([c(1)], "")


def test_deep_chain_of_200k_given_children_first_is_fast():
    n = 200_000
    comments = [c(i, i - 1, cat=True) for i in range(n - 1, 0, -1)]
    comments.append(c(0, None, cat=False, dog=True))
    start = time.perf_counter()
    gone = cf.comments_to_exclude(comments, "cat")
    kept = cf.visible_comments(comments, "dog")
    elapsed = time.perf_counter() - start
    assert len(gone) == n
    assert gone[0] == n - 1 and gone[-1] == 0
    assert kept == [0]
    assert elapsed < 2.0

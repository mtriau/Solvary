from generate_parens import generate_parens


def test_two_pairs():
    assert sorted(generate_parens(2)) == ["(())", "()()"]


def test_zero_pairs():
    assert generate_parens(0) == [""]


def test_one_pair():
    assert generate_parens(1) == ["()"]


def test_three_pairs():
    assert sorted(generate_parens(3)) == ["((()))", "(()())", "(())()", "()(())", "()()()"]


def test_catalan_counts_and_no_duplicates():
    for n, catalan in [(4, 14), (5, 42), (6, 132)]:
        result = generate_parens(n)
        assert len(result) == catalan
        assert len(set(result)) == catalan


def test_every_result_is_balanced():
    for s in generate_parens(5):
        level = 0
        for ch in s:
            level += 1 if ch == "(" else -1
            assert level >= 0
        assert level == 0

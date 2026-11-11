from clean_palindrome import is_palindrome


def test_example_true():
    assert is_palindrome("A man, a plan, a canal: Panama") is True


def test_example_false():
    assert is_palindrome("race a car") is False


def test_empty_and_punctuation_only():
    assert is_palindrome("") is True
    assert is_palindrome(".,!") is True


def test_digits_count():
    assert is_palindrome("1a1") is True
    assert is_palindrome("1a2") is False


def test_case_insensitive():
    assert is_palindrome("Aa") is True


def test_single_character():
    assert is_palindrome("x") is True

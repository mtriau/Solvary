from snake_to_camel import snake_to_camel


def test_example():
    assert snake_to_camel("hello_world") == "helloWorld"


def test_three_words():
    assert snake_to_camel("http_response_code") == "httpResponseCode"


def test_single_word_unchanged():
    assert snake_to_camel("single") == "single"


def test_empty():
    assert snake_to_camel("") == ""


def test_short_words():
    assert snake_to_camel("a_b_c") == "aBC"

from app.llm import estimate_tokens

def test_empty_text_has_zero_tokens():
    assert estimate_tokens("") == 0

def test_nonempty_text_has_positive_estimate():
    assert estimate_tokens("hello world") >= 1

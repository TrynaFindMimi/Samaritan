from output import filter


def test_filter_removes_emoji():
    out = filter.filter_output("hola 😊!")
    assert "😊" not in out
    assert "!" not in out


def test_filter_replaces_exclamation():
    out = filter.filter_output("test!")
    assert "!" not in out


def test_validate_format():
    assert filter.validate_format("ANALYZING test COMPLETE") == True


def test_filter_preserves_not_equal():
    assert filter.filter_output("a != b") == "a != b"


def test_filter_preserves_fenced_code():
    code = "```python\nif a != b:\n    print('hola!')\n```"
    assert filter.filter_output(code) == code


def test_filter_preserves_inline_code():
    assert filter.filter_output("usa `a != b` aquí!") == "usa `a != b` aquí."


def test_validate_format_requires_complete():
    assert filter.validate_format("ANALYZING test") is False


def test_validate_format_accepts_complete_with_period():
    assert filter.validate_format("ANALYZING test COMPLETE.") is True

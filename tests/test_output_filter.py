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


def test_finalize_output_adds_state_and_complete():
    out = filter.finalize_output("hola")
    assert out == "ANALYZING\nhola\nCOMPLETE"
    assert filter.validate_format(out) is True


def test_finalize_output_is_idempotent():
    text = "ANALYZING\nhola\nCOMPLETE"
    assert filter.finalize_output(text) == text


def test_finalize_output_uses_executing_for_actions():
    out = filter.finalize_output("ACCIÓN: borrar\nIMPACTO: alto\nAUTHORIZE? [Y/N]")
    assert out.startswith("EXECUTING")
    assert out.endswith("COMPLETE")


def test_finalize_output_empty():
    assert filter.finalize_output("") == "ANALYZING\nCOMPLETE"

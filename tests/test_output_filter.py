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

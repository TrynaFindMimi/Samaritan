from data import validators


def test_has_emoji():
    assert validators.has_emoji("hola 😊") == True
    assert validators.has_emoji("hola") == False


def test_contains_exclamation():
    assert validators.contains_exclamation("hola!") == True
    assert validators.contains_exclamation("hola¡") == True
    assert validators.contains_exclamation("hola.") == False


def test_python_code_passes_ast():
    code = "def foo():\n    return 1"
    assert validators.python_code_passes_ast(f"```python\n{code}\n```") == True
    bad = "def foo(\n    return 1"
    assert validators.python_code_passes_ast(f"```python\n{bad}\n```") == False

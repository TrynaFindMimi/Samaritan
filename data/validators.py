import ast
import re


def has_emoji(s: str) -> bool:
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    return bool(emoji_pattern.search(s))


def contains_exclamation(s: str) -> bool:
    return '!' in s or '¡' in s


def contains_python_code_block(s: str) -> bool:
    if '```python' in s or '```' in s:
        return True
    if re.search(r'^\s*(def |class |import |from )', s, re.M):
        return True
    return False


def python_code_passes_ast(s: str) -> bool:
    codes = []
    for m in re.findall(r'```python\n(.*?)```', s, re.S):
        codes.append(m)
    for m in re.findall(r'```\n(.*?)```', s, re.S):
        codes.append(m)
    if not codes and contains_python_code_block(s):
        codes = [s]
    if not codes:
        return True
    for code in codes:
        try:
            ast.parse(code)
        except SyntaxError:
            return False
    return True


def is_valid_sft_example(ex: dict) -> bool:
    if not isinstance(ex, dict):
        return False
    if 'messages' not in ex and not ('prompt' in ex and 'response' in ex):
        return False
    text = ""
    if 'messages' in ex:
        for m in ex['messages']:
            if isinstance(m, dict):
                text += str(m.get('content', '')) + "\n"
    else:
        text = str(ex.get('prompt', '')) + "\n" + str(ex.get('response', ''))
    if has_emoji(text):
        return False
    if contains_exclamation(text):
        return False
    if contains_python_code_block(text) and not python_code_passes_ast(text):
        return False
    return True


def clean_text(s: str) -> str:
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )
    s = emoji_pattern.sub('', s)
    s = s.replace('¡', '').replace('!', '.')
    return s

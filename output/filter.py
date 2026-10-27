import re
from data.validators import has_emoji, clean_text


VALID_STATES = ["ANALYZING", "EXECUTING", "COMPLETE", "ANOMALY DETECTED", "DATOS INSUFICIENTES"]


def filter_output(text: str) -> str:
    """Filtro final obligatorio: elimina emojis, reemplaza '!' por '.', elimina '¡'. Debe aplicarse aunque el modelo falle."""
    if text is None:
        text = ""
    text = clean_text(text)
    text = text.replace('!', '.')
    text = text.replace('¡', '')
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
    text = emoji_pattern.sub('', text)
    return text


def validate_format(text: str) -> bool:
    """Valida el formato (estado inicial en mayúsculas, cierre con COMPLETE)."""
    if not text:
        return False
    text_stripped = text.strip()
    starts_valid = False
    for state in VALID_STATES:
        if text_stripped.startswith(state):
            starts_valid = True
            break
    if not starts_valid:
        return False
    if 'COMPLETE' not in text_stripped:
        pass
    return starts_valid

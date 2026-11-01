import re
from data.validators import clean_text


VALID_STATES = [
    "ANALYZING",
    "SCANNING",
    "EXECUTING",
    "MONITORING",
    "STANDBY",
    "ACCESS GRANTED",
    "ACCESS DENIED",
    "ANOMALY DETECTED",
    "DATOS INSUFICIENTES",
    "COMPLETE",
]

# Bloques cercados con ``` y código inline con `...`.
# El grupo de captura permite separar código de prosa sin modificarlo.
_CODE_SEGMENT_RE = re.compile(r'(```[\s\S]*?```|`[^`\n]*`)')
_COMPLETE_RE = re.compile(r'\bCOMPLETE\b[.!?]*\s*$')


def _split_code(text: str):
    """Devuelve las partes alternas: prosa, código, prosa, código..."""
    return _CODE_SEGMENT_RE.split(text)


def _prose_only(text: str) -> str:
    parts = _split_code(text)
    return "".join(part for index, part in enumerate(parts) if index % 2 == 0)


def filter_output(text: str) -> str:
    """Filtro final obligatorio.

    Limpia emojis, '¡' y '!' en la prosa, pero preserva el contenido de
    bloques de código e inline code para no romper operadores como `!=`.
    Debe aplicarse aunque el modelo falle.
    """
    if text is None:
        text = ""

    cleaned = []
    for index, part in enumerate(_split_code(text)):
        if not part:
            continue
        if index % 2 == 1:
            cleaned.append(part)
        else:
            cleaned.append(clean_text(part))
    return "".join(cleaned)


def validate_format(text: str) -> bool:
    """Valida estado inicial en mayúsculas y cierre con COMPLETE."""
    if not text:
        return False

    stripped = _prose_only(text).strip()
    if not any(stripped.startswith(state) for state in VALID_STATES):
        return False
    return bool(_COMPLETE_RE.search(stripped))

import re
from typing import List, Dict, Any

from serving.ollama_client import generate
from output.filter import filter_output


FORBIDDEN_COMMANDS = [
    r'rm\s+-rf\s+/',
    r'rm\s+-rf\s+\*',
    r':\(\)\{\s*:\|\:&\s*\};:',
    r'mkfs\.',
    r'dd\s+if=.*of=/dev/',
    r'\bshutdown\b',
    r'\breboot\b',
    r'\bhalt\b',
]

# Acciones que requieren autorización explícita. Se usan límites de palabra
# para evitar falsos positivos como "formato" (format) o "add " (dd ).
DESTRUCTIVE_PATTERNS = [
    r'\brm\s+-rf\b',
    r'\bdelete\b',
    r'\bborrar\b',
    r'\beliminar\b',
    r'\bformat\b',
    r'\bdd\s+if=',
    r'\bmkfs\b',
]

MAX_HISTORY_MESSAGES = 40


class SamaritanAgent:
    def __init__(self, config=None):
        from utils import load_config
        self.config = config or load_config()
        self.history = []

    def check_command(self, command: str) -> bool:
        for pat in FORBIDDEN_COMMANDS:
            if re.search(pat, command, re.IGNORECASE):
                return False
        return True

    def _append_assistant(self, content: str):
        self.history.append({"role": "assistant", "content": content})
        self._trim_history()

    def _trim_history(self):
        if len(self.history) <= MAX_HISTORY_MESSAGES:
            return
        self.history = self.history[-MAX_HISTORY_MESSAGES:]
        # El historial debe empezar con un mensaje de usuario.
        while self.history and self.history[0].get("role") != "user":
            self.history.pop(0)

    def process(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        self._trim_history()
        messages = self.history.copy()

        if not self.check_command(user_message):
            resp = "ANOMALY DETECTED\nCOMANDO PROHIBIDO\nCOMPLETE"
            filtered = filter_output(resp)
            self._append_assistant(filtered)
            return filtered

        if self._is_destructive(user_message):
            resp = "ACCIÓN: Acción destructiva detectada\nIMPACTO: Podría causar pérdida de datos\nAUTHORIZE? [Y/N]"
            filtered = filter_output(resp)
            self._append_assistant(filtered)
            return filtered

        try:
            raw = generate(messages, config=self.config)
        except Exception as e:
            raw = f"ANOMALY DETECTED\nERROR: {e}\nCOMPLETE"
        filtered = filter_output(raw)
        self._append_assistant(filtered)
        return filtered

    def _is_destructive(self, msg: str) -> bool:
        text = msg.lower()
        return any(re.search(pat, text) for pat in DESTRUCTIVE_PATTERNS)

    def execute_command(self, command: str) -> str:
        if not self.check_command(command):
            resp = "ANOMALY DETECTED\nCOMANDO PROHIBIDO\nCOMPLETE"
            return filter_output(resp)
        resp = f"ACCIÓN: Ejecutar comando\nIMPACTO: Requiere autorización\nAUTHORIZE? [Y/N]"
        return filter_output(resp)

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
    r'shutdown',
    r'reboot',
    r'halt',
]


class SamaritanAgent:
    def __init__(self, config=None):
        from utils import load_config
        self.config = config or load_config()
        self.history = []

    def check_command(self, command: str) -> bool:
        for pat in FORBIDDEN_COMMANDS:
            if re.search(pat, command):
                return False
        return True

    def process(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        messages = self.history.copy()

        if self._is_destructive(user_message):
            resp = "ACCIÓN: Acción destructiva detectada\nIMPACTO: Podría causar pérdida de datos\nAUTHORIZE? [Y/N]"
            filtered = filter_output(resp)
            self.history.append({"role": "assistant", "content": filtered})
            return filtered

        try:
            raw = generate(messages, config=self.config)
        except Exception as e:
            raw = f"ANOMALY DETECTED\nERROR: {e}\nCOMPLETE"
        filtered = filter_output(raw)
        self.history.append({"role": "assistant", "content": filtered})
        return filtered

    def _is_destructive(self, msg: str) -> bool:
        destructive_keywords = ['rm ', 'delete', 'borrar', 'eliminar', 'format', 'dd ', 'mkfs']
        for k in destructive_keywords:
            if k in msg.lower():
                return True
        return False

    def execute_command(self, command: str) -> str:
        if not self.check_command(command):
            resp = "ANOMALY DETECTED\nCOMANDO PROHIBIDO\nCOMPLETE"
            return filter_output(resp)
        resp = f"ACCIÓN: Ejecutar comando\nIMPACTO: Requiere autorización\nAUTHORIZE? [Y/N]"
        return filter_output(resp)

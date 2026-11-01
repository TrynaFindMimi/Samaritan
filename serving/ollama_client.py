import json
import os
import subprocess
import requests
from typing import List, Dict, Any, Optional
from utils import load_config


def _get_host(config=None):
    cfg = config or load_config()
    return cfg.get('ollama', {}).get('host', 'http://localhost:11434')


def generate(messages: List[Dict[str, str]], model: Optional[str] = None,
             options: Optional[Dict[str, Any]] = None, config=None) -> str:
    """
    Única capa que conoce Ollama. Llama a la API local de Ollama.
    """
    cfg = config or load_config()
    host = _get_host(cfg)
    if model is None:
        model = cfg.get('ollama', {}).get('generator_model', 'samaritan')
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if options:
        payload["options"] = options
    resp = requests.post(f"{host}/api/chat", json=payload, timeout=600)
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content", "")


def unload(model: str, config=None) -> bool:
    """Descarga un modelo de la RAM llamando a Ollama."""
    cfg = config or load_config()
    host = _get_host(cfg)
    try:
        payload = {"model": model, "keep_alive": 0}
        resp = requests.post(f"{host}/api/generate", json=payload, timeout=60)
        return resp.status_code == 200
    except Exception:
        try:
            payload = {"model": model, "keep_alive": 0}
            resp = requests.post(f"{host}/api/chat", json={"model": model, "messages": [], "keep_alive": 0}, timeout=60)
            return resp.status_code == 200
        except Exception:
            return False


def create_model(model_name: str, modelfile_path: str, config=None) -> bool:
    """Crea un modelo en Ollama a partir de un Modelfile.

    Se usa el CLI de Ollama porque /api/create cambió: las versiones nuevas
    esperan los campos "from"/"files" en vez del antiguo "modelfile".
    El CLI sigue aceptando el Modelfile completo y además soporta ADAPTER.
    """
    cfg = config or load_config()
    host = _get_host(cfg)
    try:
        env = os.environ.copy()
        env["OLLAMA_HOST"] = host
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", modelfile_path],
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            print(f"ERROR create_model: {detail}")
            return False
        return True
    except Exception as e:
        print(f"ERROR create_model: {e}")
        return False

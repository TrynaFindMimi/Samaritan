import json
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
    cfg = config or load_config()
    host = _get_host(cfg)
    try:
        with open(modelfile_path) as f:
            content = f.read()
        payload = {"name": model_name, "modelfile": content}
        resp = requests.post(f"{host}/api/create", json=payload, timeout=600)
        return resp.status_code == 200
    except Exception as e:
        print(f"ERROR create_model: {e}")
        return False

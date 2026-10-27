"""
Capa de datos (data/)
Genera, valida y versiona datasets (SFT y DPO) con Ollama
"""
from .dataset import build_datasets

__all__ = ["build_datasets"]

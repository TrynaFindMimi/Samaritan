"""
Capa de serving (serving/)
Única capa que conoce Ollama. Expone generate() y unload().
"""
from .ollama_client import generate, unload, create_model

__all__ = ["generate", "unload", "create_model"]

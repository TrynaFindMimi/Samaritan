"""
Capa de juez offline (judge/)
Construye dataset DPO sin intervención manual
"""
from .dpo_builder import build_dpo_dataset

__all__ = ["build_dpo_dataset"]

"""
Capa de modelo (model/)
SFT con LoRA sobre Qwen/Qwen2.5-0.5B-Instruct, luego DPO opcional
"""
from .train import train_sft, train_dpo, export_gguf, merge_adapter

__all__ = ["train_sft", "train_dpo", "export_gguf", "merge_adapter"]

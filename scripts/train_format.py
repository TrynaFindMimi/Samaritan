#!/usr/bin/env python3
"""Reproduce la corrida SFT/DPO centrada en formato.

Uso:
    source .venv/bin/activate
    python scripts/train_format.py

El CLI por defecto usa data/train.jsonl y data/dpo.jsonl con 1 época.
Este script usa data/train_format.jsonl y data/dpo_format.jsonl, con
5 épocas de SFT, y luego fusiona/exporta el adaptador.
"""
import os
import shutil
from datetime import datetime
from pathlib import Path

from model.train import export_gguf, merge_adapter, train_dpo, train_sft
from utils import load_config

ROOT = Path(__file__).resolve().parent.parent


def main():
    os.chdir(ROOT)

    cfg = load_config()
    cfg['data']['train_out'] = 'data/train_format.jsonl'
    cfg['data']['dpo_out'] = 'data/dpo_format.jsonl'
    cfg['training']['sft']['num_train_epochs'] = 5
    cfg['training']['dpo']['num_train_epochs'] = 1

    adapter = ROOT / 'model' / 'lora_adapter'
    if adapter.exists():
        backup = ROOT / 'model' / f"lora_adapter_backup_{datetime.now():%Y%m%d_%H%M%S}"
        shutil.copytree(adapter, backup)
        print(f'Backup del adaptador: {backup}')

    print(f"SFT: {cfg['data']['train_out']} ({cfg['training']['sft']['num_train_epochs']} épocas)")
    train_sft(cfg)

    print(f"DPO: {cfg['data']['dpo_out']} ({cfg['training']['dpo']['num_train_epochs']} época)")
    train_dpo(cfg)

    print('Fusionando adaptador...')
    merge_adapter(cfg)

    print('Exportando GGUF...')
    export_gguf(cfg)

    print('Listo. Ejecuta: python main.py create-model')


if __name__ == '__main__':
    main()

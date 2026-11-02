#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python -c "from model.train import merge_adapter; merge_adapter()"
python -c "from model.train import export_gguf; export_gguf()"
python main.py create-model

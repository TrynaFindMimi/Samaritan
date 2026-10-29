#!/usr/bin/env bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

ollama pull qwen2.5:0.5b
ollama rm samaritan 2>/dev/null || true
ollama create samaritan -f Modelfile

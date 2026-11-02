#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
source .venv/bin/activate

python -m pytest -q

if ! show_output="$(ollama show samaritan 2>/dev/null)"; then
  echo "ERROR: el modelo 'samaritan' no existe en Ollama. Ejecuta: python main.py create-model" >&2
  exit 1
fi

if ! grep -q 'F16' <<<"$show_output"; then
  echo "ERROR: se esperaba un modelo F16 en Ollama" >&2
  exit 1
fi

python - <<'PY'
from output.filter import finalize_output, validate_format
from serving.ollama_client import generate

response = generate(
    [{"role": "user", "content": "Responde solo: OK"}],
    model="samaritan",
    options={"num_predict": 32},
)
final = finalize_output(response)
print("raw:", repr(response))
print("final:", repr(final))
assert validate_format(final), "La salida final no cumple el contrato"
print("SMOKE OK")
PY

# Quickstart - SAMARITAN

## Requisitos
- Python 3.12+ con venv
- Ollama corriendo en `http://localhost:11434`
- RAM >= 4GB disponible (recomendado para entrenar)
- Solo CPU

## Instalación

```bash
cd /home/mimi/Samaritan
python -m venv .venv
source .venv/bin/activate  # o fish equivalente
pip install -r requirements.txt
```

## Uso

### 1. Construir datasets
```bash
PYTHONPATH=/home/mimi/Samaritan python main.py build-data
```
Lee `data/dataset_sft.jsonl` y genera `data/train.jsonl` y `data/eval.jsonl`.

### 2. Entrenar SFT (LoRA)
```bash
PYTHONPATH=/home/mimi/Samaritan python main.py train-sft
```
Entrena con LoRA r=16, alpha=32, fp32, CPU. Guarda adaptador en `model/lora_adapter/`.

### 3. Crear modelo en Ollama
```bash
PYTHONPATH=/home/mimi/Samaritan python main.py create-model
# o directamente:
ollama create samaritan -f serving/Modelfile
```

### 4. Construir dataset DPO con juez offline
```bash
PYTHONPATH=/home/mimi/Samaritan python main.py build-dpo
```
Genera candidatos, puntúa con juez local, construye pares DPO en `data/dpo.jsonl`.

### 5. Entrenar DPO
```bash
PYTHONPATH=/home/mimi/Samaritan python main.py train-dpo
```
DPO con TRL sobre adaptador SFT.

### 6. Evaluación
```bash
PYTHONPATH=/home/mimi/Samaritan python main.py eval
```

## Probar el modelo

```python
from serving.ollama_client import generate
from output.filter import filter_output

resp = generate([{"role": "user", "content": "Analiza el estado del sistema"}], model="samaritan")
print(filter_output(resp))
```

## Usar el agente

```python
from agent.agent import SamaritanAgent
from ui.tui import SamaritanTUI

agent = SamaritanAgent()
tui = SamaritanTUI()
resp = agent.process("Analiza el estado del sistema")
tui.show(resp)
```

## Tests

```bash
PYTHONPATH=/home/mimi/Samaritan /home/mimi/Samaritan/.venv/bin/python -c "
# ejecutar tests manualmente
from data import validators
from judge import dpo_builder
from output import filter
# ... ver tests/test_*.py
"
```

## Notas importantes
- Solo `serving/` conoce Ollama
- Todo corre offline
- RAM se monitorea con `utils.check_ram_before()`
- Si RAM > 5.5 GiB se avisa para reducir `max_seq_length` o tamaño
- El filtro de salida se aplica SIEMPRE

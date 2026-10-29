# Inicio rapido - SAMARITAN

## Requisitos

- Python 3.10 o superior
- Ollama en `http://localhost:11434`
- CPU suficiente para `qwen2.5:0.5b`

## Instalacion

```bash
cd /home/mimi/Samaritan
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Crear el modelo

```bash
./serving/create_model.sh
```

El script descarga `qwen2.5:0.5b`, elimina el modelo `samaritan` anterior y lo
crea de nuevo con el system prompt de `serving/Modelfile`.

Equivalente manual:

```bash
ollama pull qwen2.5:0.5b
ollama rm samaritan
ollama create samaritan -f serving/Modelfile
```

## Usar

```bash
python main.py
python main.py query "Analiza el estado del sistema"
python main.py ask "Analiza el estado del sistema"
```

## Tests

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest tests/ -q
```

## Entrenamiento opcional

Solo si quieres ajustar el estilo del modelo. No es necesario para usar el
agente.

```bash
python main.py build-data
python main.py train-sft
python main.py create-model
python main.py build-dpo
python main.py train-dpo
python main.py eval
```

Ver [TRAINING.md](TRAINING.md) para los detalles.

## Notas

- Solo `serving/` conoce Ollama.
- Todo corre offline.
- `output/filter_output()` se aplica siempre, incluso si el modelo falla.
- `utils.check_ram_before()` avisa si el sistema se queda sin RAM.

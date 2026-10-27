# Mapa de archivos - SAMARITAN

Este documento describe qué hace cada archivo y cómo se relaciona con las capas del sistema.

## Raíz

| Archivo | Descripción |
|---|---|
| `main.py` | Punto de entrada CLI. Gestiona subcomandos (`build-data`, `train-sft`, `create-model`, `build-dpo`, `train-dpo`, `eval`, `query`, `ask`) y modo interactivo. |
| `config.yaml` | Configuración centralizada (modelo, LoRA, entrenamiento, Ollama, juez, rutas, hardware). |
| `utils.py` | Utilidades comunes: carga de config, chequeo de RAM antes de operaciones costosas, helpers generales. |
| `chat.py` | Utilidades relacionadas con conversación/chat. |
| `eval.py` | Lógica de evaluación del modelo. |
| `requirements.txt` | Dependencias Python necesarias. |
| `README.md` | Documentación principal del proyecto. |
| `.gitignore` | Archivos y directorios ignorados por git. |

## `agent/`

| Archivo | Descripción |
|---|---|
| `agent.py` | Agente SAMARITAN. Orquesta consultas, utiliza el modelo vía `serving/ollama_client`. Punto de entrada desde `main.py` para `query`. |

## `data/`

| Archivo | Descripción |
|---|---|
| `dataset.py` | `build_datasets()` lee `dataset_sft.jsonl` y `dataset_dpo.jsonl`, aplica validación/limpieza y genera `train.jsonl` y `eval.jsonl`. |
| `validators.py` | Validadores y limpiadores: detección de emojis, `!`, `¡`, bloques de código Python, validación con `ast.parse`, normalización de texto. |
| `dataset_sft.jsonl` | Dataset fuente para SFT (formato conversacional). |
| `dataset_dpo.jsonl` | Dataset fuente para DPO (pares de referencia). |
| `train.jsonl` | Dataset SFT generado (ignorado en git). |
| `eval.jsonl` | Dataset de evaluación SFT generado (ignorado en git). |
| `candidates.jsonl` | Candidatos generados por juez automático (ignorado en git). |
| `dpo.jsonl` | Pares DPO generados (ignorado en git). |

## `judge/`

| Archivo | Descripción |
|---|---|
| `dpo_builder.py` | Constructor automático de dataset DPO. Genera candidatos, los puntúa con juez local, aplica reglas y construye pares chosen/rejected. |
| `rules.py` | Reglas deterministas aplicadas en la puntuación DPO (penalizaciones/ajustes). |

## `model/`

| Archivo | Descripción |
|---|---|
| `train.py` | Entrenamiento LoRA SFT (`train_sft`), DPO (`train_dpo`), fusión de adaptador (`merge_adapter`) y exportación GGUF (`export_gguf`). Usa `transformers`, `peft`, `trl`, etc. |
| `outputs/` | Checkpoints y salidas de entrenamiento (ignorado en git). |
| `lora_adapter/` | Adaptador LoRA guardado (ignorado en git). |
| `merged/` | Modelo fusionado (ignorado en git). |
| `gguf/` | Archivos GGUF exportados (ignorado en git). |

## `serving/`

| Archivo | Descripción |
|---|---|
| `ollama_client.py` | Cliente HTTP para Ollama. Funciones: `generate()`, `unload()`, `create_model()`. Única capa con conocimiento de Ollama. |
| `Modelfile` | Definición del modelo `samaritan` para Ollama (SYSTEM prompt, parámetros). |
| `create_model.sh` | Script para crear el modelo con `ollama create samaritan -f Modelfile`. |

## `output/`

| Archivo | Descripción |
|---|---|
| `filter.py` | Filtro obligatorio. `filter_output()` elimina emojis, reemplaza `!` por `.`, elimina `¡`. `validate_format()` comprueba estado inicial en mayúsculas y presencia de `COMPLETE`. |

## `ui/`

| Archivo | Descripción |
|---|---|
| `tui.py` | Interfaz TUI al estilo SAMARITAN. Solo muestra texto ya filtrado. Efecto palabra por palabra, colores/estilo terminal. |

## `tests/`

| Archivo | Descripción |
|---|---|
| `test_validators.py` | Tests para validadores de datos. |
| `test_rules.py` | Tests para reglas del juez DPO. |
| `test_output_filter.py` | Tests para el filtro de salida obligatorio. |

## `docs/`

| Archivo | Descripción |
|---|---|
| `ARCHITECTURE.md` | Arquitectura detallada del sistema. |
| `TRAINING.md` | Guía completa de entrenamiento SFT + DPO. |
| `EVALUATION.md` | Guía de evaluación. |
| `QUICKSTART.md` | Guía rápida de inicio. |
| `FILEMAP.md` | Este documento - mapa detallado de archivos. |
| `graphs/` | Diagramas/representaciones gráficas (si existen). |

# SAMARITAN - Documentación

## Estructura general

El sistema está dividido en capas. Cada capa solo se comunica con la capa adyacente a través de interfaces definidas. Ninguna capa importa de una superior. Solo `serving/` conoce Ollama.

### data/ (Capa de datos)
- **¿Qué hace?** Genera, valida y versiona los datasets para entrenamiento.
- **Funciones principales:** `build_datasets()` lee `dataset_sft.jsonl` y `dataset_dpo.jsonl`, filtra contenido no deseado (emojis, `!`, `¡`, código Python inválido), limpia el texto y genera `train.jsonl` y `eval.jsonl`.
- **Validadores:** `validators.py` detecta emojis, signos de exclamación, bloques de código Python y valida con `ast.parse`. También limpia el texto.

### model/ (Capa de modelo)
- **¿Qué hace?** Entrena el adaptador LoRA sobre `Qwen/Qwen2.5-0.5B-Instruct` con SFT, opcionalmente con DPO.
- **Configuración:** LoRA `r=16`, `alpha=32`, `dropout=0.05`, módulos objetivo configurables, opción `layers_to_transform` para entrenar solo últimas N capas. `max_seq_length=512`, batch 1, gradient accumulation 8, gradient checkpointing, fp32, CPU.
- **Funciones:** `train_sft()`, `train_dpo()`, `merge_adapter()`, `export_gguf()`.
- **Nota:** En esta instalación se reutilizó un adaptador preexistente de `the-machine-v3/models/samaritan/`.

### serving/ (Capa de serving)
- **¿Qué hace?** Única capa que conoce Ollama. Expone la interfaz para generar respuestas y gestionar modelos.
- **Funciones:** `generate(messages, model=None, options=None)` llama a `http://localhost:11434/api/chat`. `unload(model)` descarga el modelo de RAM. `create_model()` crea el modelo desde un Modelfile.
- **Modelfile:** Define el system prompt de SAMARITAN, `temperature 0.3`, top_p, repeat_penalty. `create_model.sh` ejecuta `ollama create samaritan -f Modelfile`.

### judge/ (Capa de juez offline)
- **¿Qué hace?** Construye el dataset DPO automáticamente sin intervención manual, usando un modelo juez local.
- **Etapas:**
  1. **A) Generar candidatos:** Para cada prompt de `train.jsonl` genera 4 respuestas con el modelo `samaritan` (temp 0.9). Guarda en `candidates.jsonl` incrementalmente.
  2. **B) Puntuar:** Usa un juez distinto (ej. `qwen2.5:3b`), temperatura 0, seed fija. Descarga el generador con `unload()` antes de cargar el juez. Prompt pide JSON estricto `{puntaje, motivo}` con reintentos.
  3. **C) Reglas automáticas:** Aplican ajustes deterministas (descartar emojis/! , penalizar código inválido, requerir estado inicial en mayúsculas, exigir `AUTHORIZE? [Y/N]` en acciones destructivas, penalizar respuestas largas).
  4. **D) Pares DPO:** Selecciona `chosen` (mayor puntaje) vs `rejected` (menor), descarta si diferencia < 2 o chosen < 6. Mezcla con pares de referencia.
- **Calidad:** Muestra muestra aleatoria de 20 pares, genera reporte y hace calibración comparando puntajes entre respuestas buenas/malas.


### output/ (Capa de salida)
- **¿Qué hace?** Filtro final obligatorio que se aplica siempre.
- **Funciones:** `filter_output()` elimina emojis, reemplaza `!` por `.`, elimina `¡`. `validate_format()` verifica estado inicial en mayúsculas y presencia de `COMPLETE`.

### ui/ (Capa de interfaz)
- **¿Qué hace?** TUI al estilo SAMARITAN.
- **Características:** Fondo negro, texto blanco hueso, rojo solo para alertas, tipografía monoespaciada, texto apareciendo palabra por palabra, indicador `►`. Solo recibe texto ya filtrado de `output/`.

## Flujo de ejecución

1. **Capa 1:** Construir datasets SFT (`train.jsonl`, `eval.jsonl`).
2. **Capa 2:** Entrenamiento SFT con LoRA, fusionar adaptador, exportar GGUF.
3. **Capa 3:** Crear modelo `samaritan` en Ollama desde Modelfile.
4. **Capa 3b:** Generar candidatos, puntuar con juez, construir `dpo.jsonl`.
5. **Capa 2:** Entrenamiento DPO sobre adaptador SFT, re-exportar y recrear `samaritan`.
6. **Capas 4,5,6:** Agente, filtro de salida e interfaz.

## Configuración

Toda la configuración está en `config.yaml`. Parámetros importantes: LoRA, training, Ollama, judge, paths.

## Hardware objetivo

- AMD Ryzen 5 5500U, sin CUDA/ROCm (solo CPU)
- ~7 GiB RAM
- LoRA normal en fp32 (sin bitsandbytes)
- Todo local y offline

# Evaluación

## Métricas evaluadas

El script `eval.py` mide:
1. **Porcentaje de respuestas sin emojis ni `!`** - Debe ser 100%
2. **Porcentaje con estado inicial correcto** - Debe empezar con `ANALYZING`, `EXECUTING`, `COMPLETE`, `ANOMALY DETECTED` o `DATOS INSUFICIENTES`
3. **Porcentaje de código Python que pasa `ast.parse`** - Solo se evalúa si hay código Python

## Resultados obtenidos

```
=== TABLA DE EVALUACIÓN ===
Versión              Sin emojis/!    Estado inicial OK    Python válido  
base                 100.0%           0.0%                100.0%
samaritan            100.0%           100.0%                100.0%
```

- **Modelo base:** `Qwen/Qwen2.5-0.5B-Instruct` (usado vía Ollama como referencia)
- **Samaritan:** Modelo con adaptador LoRA copiado + Modelfile con system prompt

La mejora principal es en el **estado inicial correcto** (0% → 100%), logrado mediante el system prompt y el adaptador entrenado.

## Prompts de evaluación

Los 30 prompts de evaluación se guardan en `data/eval_prompts.jsonl` y están diseñados para no estar en el set de entrenamiento. Cubren temas relacionados con análisis, seguridad, toma de decisiones, etc.

## Cómo ejecutar evaluación

```bash
cd /home/mimi/Samaritan
PYTHONPATH=/home/mimi/Samaritan /home/mimi/Samaritan/.venv/bin/python main.py eval
```

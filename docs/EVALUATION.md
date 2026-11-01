# Evaluación

## Métricas evaluadas

El script `eval.py` mide:
1. **Porcentaje de respuestas sin emojis ni `!`** - Debe ser 100%
2. **Porcentaje con estado inicial correcto** - Debe empezar con `ANALYZING`, `SCANNING`, `EXECUTING`, `MONITORING`, `STANDBY`, `ACCESS GRANTED`, `ACCESS DENIED`, `ANOMALY DETECTED`, `DATOS INSUFICIENTES` o `COMPLETE`
3. **Porcentaje de código Python que pasa `ast.parse`** - Solo se evalúa si hay código Python

## Resultados obtenidos

Última ejecución con `qwen2.5:0.5b` local:

```
=== TABLA DE EVALUACIÓN ===
Versión              Sin emojis/!    Estado inicial OK    Python válido  
base                 83.3%           0.0%                100.0%
samaritan            90.0%           0.0%                100.0%
```

- **Modelo base:** `qwen2.5:0.5b` (Ollama, configurado en `ollama.base_model`)
- **Samaritan:** `qwen2.5:0.5b` + system prompt. El adaptador LoRA no está desplegado porque Ollama 0.40.12 no soporta `ADAPTER`; ver `docs/DEPLOYMENT.md`.

El **estado inicial correcto sigue en 0%**: el modelo 0.5B no está siguiendo el formato `ANALYZING ... COMPLETE`. No es un fallo del evaluador; es una limitación del modelo/prompt. Para mejorarlo hace falta ajustar el prompt o desplegar el adaptador mediante GGUF.

## Prompts de evaluación

Los 30 prompts de evaluación se guardan en `data/eval_prompts.jsonl` y están diseñados para no estar en el set de entrenamiento. Cubren temas relacionados con análisis, seguridad, toma de decisiones, etc.

## Cómo ejecutar evaluación

```bash
cd /Users/leonardocarrillo/AIProj/Samaritan
python3 main.py eval
```

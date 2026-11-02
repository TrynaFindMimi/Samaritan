# Evaluación

## Métricas evaluadas

El script `eval.py` mide dos niveles: **raw** (lo que genera el modelo) y **final** (lo que recibe el usuario después de `finalize_output()`).

1. **Sin emojis ni `!`**: respuestas limpias de estilo.
2. **Raw Inicio (`starts_with_state_pct`)**: la respuesta cruda empieza exactamente con un estado válido.
3. **Raw Estado (`contains_state_pct`)**: la respuesta cruda menciona un estado válido en cualquier parte.
4. **Raw Formato (`format_valid_pct`)**: la respuesta cruda pasa `validate_format()` (inicio con estado + cierre con `COMPLETE`).
5. **Final Inicio (`final_starts_with_state_pct`)**: la respuesta final empieza con estado.
6. **Final OK (`final_format_valid_pct`)**: la respuesta final pasa `validate_format()`.
7. **Python válido**: porcentaje de código Python que pasa `ast.parse`. Si no hay código Python, se reporta `100.0%` por defecto.

La evaluación usa `temperature=0` y `num_predict=256` para evitar generaciones runaway.

## Resultados obtenidos

Última ejecución con `qwen2.5:0.5b` y `samaritan` desplegado desde GGUF F16:

```
=== TABLA DE EVALUACIÓN ===
Versión            Sin emojis/!  Raw Inicio  Raw Estado  Raw Formato  Final Inicio  Final OK   Python
base                      83.3%        0.0%        0.0%         0.0%        100.0%    100.0%   100.0%
samaritan                100.0%       73.3%       96.7%        73.3%        100.0%    100.0%   100.0%
```

- **Modelo base:** `qwen2.5:0.5b` (Ollama, configurado en `ollama.base_model`).
- **Samaritan:** modelo base + adaptador LoRA entrenado con SFT y DPO sobre un conjunto centrado en formato, fusionado y desplegado como `samaritan-f16.gguf`; ver `docs/DEPLOYMENT.md`.

### Cómo interpretar los números

- **Raw Inicio = 73,3%**: el modelo empieza con un estado válido en 22 de 30 respuestas.
- **Raw Estado = 96,7%**: el modelo menciona un estado válido en 29 de 30 respuestas.
- **Raw Formato = 73,3%**: 22 de 30 respuestas crudas cumplen inicio con estado y cierre `COMPLETE`.
- **Final Inicio = 100%** y **Final OK = 100%**: `finalize_output()` garantiza el contrato de salida para el usuario. Si falta el estado inicial, lo añade; si falta `COMPLETE`, lo agrega.
- **Python = 100%** no mide calidad si no hay código; es el valor por defecto.
- La diferencia entre raw y final es intencional: raw mide al modelo; final mide el producto.
- La mejora raw respecto de la corrida anterior (20 % / 56,7 % / 10 %) es consistente con el cambio de datos: el nuevo conjunto SFT/DPO incluye explícitamente el contrato de formato.

## Prompts de evaluación

Los 30 prompts de evaluación se guardan en `data/eval_prompts.jsonl` y están diseñados para no estar en el set de entrenamiento. Cubren temas relacionados con análisis, seguridad, toma de decisiones, etc.

## Cómo ejecutar evaluación

```bash
cd /Users/leonardocarrillo/AIProj/Samaritan
source .venv/bin/activate
python main.py eval
```

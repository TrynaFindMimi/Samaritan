# Evaluación

## Estado de esta revisión

Esta evaluación se midió sobre el estado actual del repositorio (2 de noviembre de 2026) con:

- **30 prompts fijos** de `data/eval_prompts.jsonl`.
- `temperature=0` y `num_predict=256`.
- Ollama 0.40.3.
- Tres variantes: modelo base por defecto, modelo base con el prompt desplegado y Samaritan desplegado.

Las cifras anteriores de `docs/EVALUATION.md` (base 83,3 % y Samaritan 73,3 %) corresponden a una corrida previa y se mencionan solo como referencia histórica. La fila de “base 100 %” que aparecía en versiones antiguas del informe coincidía con una corrida en la que 30 de 30 respuestas fueron errores HTTP 404 contabilizados como respuestas; no se usa en este documento.

## Métricas evaluadas

`eval.py` mide dos niveles:

- **Raw:** lo que genera el modelo antes del filtro.
- **Final:** lo que recibe el usuario después de `finalize_output()`.

Las métricas son:

1. **Sin emojis ni `!`:** respuestas limpias de estilo.
2. **Raw Inicio (`starts_with_state_pct`):** la respuesta cruda empieza exactamente con un estado válido.
3. **Raw Estado (`contains_state_pct`):** la respuesta cruda menciona un estado válido en cualquier parte.
4. **Raw Formato (`format_valid_pct`):** la respuesta cruda pasa `validate_format()` (inicio con estado + cierre con `COMPLETE`).
5. **Final Inicio (`final_starts_with_state_pct`):** la respuesta final empieza con estado.
6. **Final OK (`final_format_valid_pct`):** la respuesta final pasa `validate_format()`.
7. **Python válido:** porcentaje de bloques de código Python que pasan `ast.parse`. Si no hay código, se reporta `100.0%` por defecto; por eso se informa el denominador.

## Resultados medidos

```
=== TABLA DE EVALUACIÓN ===
Versión            Sin emojis/!  Raw Inicio  Raw Estado  Raw Formato  Final Inicio  Final OK   Python
base                      86.7%        0.0%        0.0%         0.0%        100.0%    100.0%   100.0%  (n=0)
base + prompt            100.0%       90.0%       90.0%        36.7%        100.0%    100.0%   100.0%  (n=3)
samaritan                100.0%      100.0%      100.0%       100.0%        100.0%    100.0%   100.0%  (n=2)
```

- **Modelo base por defecto:** `qwen2.5:0.5b` sin el system prompt desplegado.
- **Modelo base + prompt:** el mismo modelo con el system prompt que se usó en el despliegue.
- **Samaritan:** modelo base + adaptador LoRA fusionado y desplegado como `samaritan-f16.gguf`.

### Cómo interpretar los números

- **Raw Inicio = 90 % en base+prompt:** el prompt por sí solo induce el estado inicial en 27 de 30 respuestas. Parte de la mejora de Samaritan puede provenir del prompt, no solo del adaptador.
- **Raw Formato = 36,7 % en base+prompt:** el prompt induce el inicio, pero no basta para cerrar con `COMPLETE` en la mayoría de los casos.
- **Raw Formato = 100 % en Samaritan:** el modelo ajustado cumple inicio y cierre en las 30 respuestas. Es evidencia descriptiva a favor del entrenamiento de formato, pero no separa SFT de DPO.
- **Final Inicio = 100 % y Final OK = 100 %:** `finalize_output()` garantiza el contrato de salida para el usuario. No mide calidad semántica.
- **Python = 100 %:** no mide calidad si no hay código. Los denominadores son 0, 3 y 2; el porcentaje no es comparable entre variantes.
- La diferencia entre raw y final es intencional: raw mide al modelo; final mide el producto.

### Tiempos observados

Los tiempos son descriptivos y corresponden a una sola corrida en CPU:

| Variante | Tiempo aproximado para 30 prompts |
|---|---:|
| Base por defecto | 225 s |
| Base + prompt | 108 s |
| Samaritan | 152 s |

No se reportan intervalos de confianza ni repeticiones.

## Prompts de evaluación

Los 30 prompts de evaluación se guardan en `data/eval_prompts.jsonl` y están diseñados para no estar en el set de entrenamiento. Cubren temas relacionados con análisis, seguridad y toma de decisiones.

## Cómo ejecutar la evaluación

```bash
cd /ruta/al/repositorio/Samaritan
source .venv/bin/activate
python main.py eval
```

`main.py eval` compara el modelo base y Samaritan. La variante **base + prompt** se midió con un script de verificación externo que aplica el system prompt desplegado; para reproducirla de forma exacta hace falta versionar ese prompt en el repositorio.

## Limitaciones

- Una sola corrida de 30 prompts no permite generalizar ni estimar variabilidad.
- No hay evaluación semántica, revisión humana ni comparación separada base/SFT/SFT+DPO.
- El prompt desplegado no está versionado en el repositorio.
- `data/dpo.jsonl` es idéntico a `data/dataset_dpo.jsonl`: 30 pares de referencia, 0 generados por el juez.
- La métrica de Python depende del número de bloques detectados.

## Figuras relacionadas

- `docs/graphs/svg/fig03_evaluacion.svg`
- `docs/graphs/svg/fig05_salida_eval.svg`
- `docs/graphs/svg/fig10_dpo_funnel.svg`

Los datos de esta tabla están en `docs/graphs/data/eval_metrics.json`.

# Gráficas para presentación

Esta carpeta está destinada a guardar gráficas generadas para la presentación.

## Gráficas sugeridas

### 1. Evolución de entrenamiento (epoch/loss)
- **Archivo:** `training_loss.png`
- **Descripción:** Curva de loss por step/epoch durante SFT y DPO
- **Fuente:** Logs de `transformers.Trainer` (se guardan en `model/outputs/`)

### 2. Comparativa de evaluación
- **Archivo:** `evaluation_comparison.png`
- **Descripción:** Barras comparando modelo base vs SFT vs DPO en las 3 métricas
- **Datos:** Ver `docs/EVALUATION.md`

### 3. Arquitectura de capas
- **Archivo:** `architecture.png`
- **Descripción:** Diagrama de las 7 capas con flujo de comunicación
- **Referencia:** Ver `docs/ARCHITECTURE.md`

### 4. Distribución de puntajes DPO
- **Archivo:** `dpo_scores.png`
- **Descripción:** Histograma de puntajes del juez antes/después de reglas
- **Fuente:** `data/scored_candidates.jsonl` (cuando se genere)

### 5. Métricas por etapa
- **Archivo:** `pipeline_metrics.png`
- **Descripción:** Flujo de datos por etapas (prompts → candidatos → pares válidos)
- **Fuente:** Reporte del juez en `judge/dpo_builder.py`

## Cómo generar

```python
import matplotlib.pyplot as plt
# Ejemplo para evaluación
versions = ['Base', 'SFT', 'DPO']
no_emoji = [100, 100, 100]
correct_state = [0, 100, 100]
python_ok = [100, 100, 100]
# ... generar gráfica
```

Nota: matplotlib puede no estar instalado. Instalar con `pip install matplotlib` si se necesita.

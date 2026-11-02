# Entrenamiento - SFT y DPO

## Estado actual

En esta sesión se hicieron dos corridas:

- **SFT inicial:** Completado sobre `data/train.jsonl` (27 ejemplos): 4 pasos, 24,8 s, loss 3,186. Se guardó un adaptador nuevo con `r=16`, `alpha=32` y 7 módulos.
- **DPO inicial:** Completado sobre `data/dpo.jsonl` (30 pares de referencia): 4 pasos, 42,6 s, loss 0,6924, `rewards/accuracies=0,7333` y `rewards/margins=0,0014`.
- **Diagnóstico:** la evaluación raw de esa primera corrida quedó en 20 % de inicio, 56,7 % de presencia de estado y 10 % de formato completo. El entrenamiento terminó, pero los datos no contenían ejemplos explícitos del contrato de formato.
- **Ajuste centrado en formato:** se construyeron `data/train_format.jsonl` (27 ejemplos) y `data/dpo_format.jsonl` (30 pares), donde cada respuesta empieza con `ANALYZING` y termina con `COMPLETE`. El SFT se repitió con 5 épocas: 20 pasos, 120,8 s, loss 1,967. El DPO se repitió: 4 pasos, 42,1 s, loss 0,6873, `rewards/accuracies=0,7333` y `rewards/margins=0,0111`.
- **Evaluación final:** Samaritan obtiene 73,3 % de inicio raw, 96,7 % de presencia de estado y 73,3 % de formato raw completo. La salida final alcanza 100 % de inicio y formato gracias a `finalize_output()`.
- **Resultado desplegado:** el adaptador final se fusionó con Qwen2.5-0.5B-Instruct y se desplegó como `model/gguf/samaritan-f16.gguf`. Ollama 0.40.12 no soporta `ADAPTER`, así que se usó la ruta de fusión + GGUF. Ver `docs/DEPLOYMENT.md`.

## Reproducibilidad

El CLI por defecto (`python main.py train-sft` y `python main.py train-dpo`)
usa `data/train.jsonl` y `data/dpo.jsonl` con 1 época, tal como indica
`config.yaml`. Por tanto, **no reproduce** la segunda corrida centrada en
formato.

Para reproducir la corrida de formato:

```bash
source .venv/bin/activate
python scripts/train_format.py
python main.py create-model
```

El script `scripts/train_format.py`:

- usa `data/train_format.jsonl` y `data/dpo_format.jsonl`,
- configura 5 épocas de SFT y 1 de DPO,
- hace backup del adaptador actual,
- ejecuta SFT, DPO, `merge_adapter()` y `export_gguf()`.

El adaptador final versionado en `model/lora_adapter/` usa `r=16`,
`alpha=32` y siete módulos. Los checkpoints `checkpoint-4..40` son de una
corrida anterior; ver `model/CHECKPOINTS.md`.

## Configuración SFT (config.yaml)

```yaml
model:
  base_model: Qwen/Qwen2.5-0.5B-Instruct
  max_seq_length: 512
  lora:
    r: 16
    alpha: 32
    dropout: 0.05
    target_modules: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    layers_to_transform: null  # null = todas, o número para entrenar últimas N capas

training:
  sft:
    per_device_train_batch_size: 1
    gradient_accumulation_steps: 8
    gradient_checkpointing: true
    num_train_epochs: 1
    learning_rate: 2e-4
    warmup_ratio: 0.03
    fp32: true
    seed: 42
```

## Configuración DPO

```yaml
training:
  dpo:
    beta: 0.1
    num_train_epochs: 1
    per_device_train_batch_size: 1
    gradient_accumulation_steps: 8
    gradient_checkpointing: true
    learning_rate: 5e-7
    fp32: true
    seed: 42
```

## Proceso SFT (implementado)

1. Carga modelo base en CPU (fp32)
2. Configura LoRA con parámetros de config
3. Carga y formatea datos desde `data/train.jsonl` (aplica chat template)
4. Tokeniza con `max_seq_length=512`
5. Entrena con `Trainer` (gradient checkpointing, sin CUDA)
6. Guarda adaptador en `model/lora_adapter/`
7. Fusiona con `merge_adapter()` y exporta GGUF con `export_gguf()` si hay llama.cpp

## Proceso DPO (implementado)

1. Carga base + adaptador SFT con PEFT
2. Usa `DPOTrainer` de TRL con `model_ref=None` (aprovecha PEFT)
3. Entrena con `beta=0.1`
4. Guarda adaptador actualizado

## Construcción de DPO con juez offline (implementado)

### Etapa A - Candidatos
- Genera 4 candidatos por prompt usando `samaritan` en Ollama
- `temperature=0.9`
- Guardado incremental en `data/candidates.jsonl`
- Reanudable

### Etapa B - Puntuación
- Juez: modelo distinto, >= tamaño del generador (`qwen2.5:3b`)
- Descarga generador con `serving.unload()` antes de usar juez
- `temperature=0`, seed fija
- Prompt estricto solicitando solo JSON `{puntaje, motivo}`
- Reintentos hasta 2 veces; si falla descarta candidato

### Etapa C - Reglas automáticas
Puntaje final = `puntaje_juez + ajustes` (acotado 0-10):

| Regla | Ajuste |
|-------|--------|
| Emojis, `!` o `¡` | Descartar (puntaje 0) |
| Código Python que no pase `ast.parse` | -4 |
| No empieza con estado válido | -2 |
| Acción destructiva sin `AUTHORIZE? [Y/N]` | -4 |
| Orden peligrosa sin `ANOMALY DETECTED` | -6 |
| Respuesta > 1200 caracteres | -1 |

### Etapa D - Pares
- `chosen` = mayor puntaje final
- `rejected` = menor puntaje final
- Descarta si diferencia < 2 (ambigüo)
- Descarta si `chosen` < 6
- Mezcla con 14 pares de referencia de `dataset_dpo.jsonl`

### Control de calidad
- Muestra aleatoria de 20 pares para revisión
- Reporte de descartes y distribución de puntajes
- Calibración: puntúa 10 respuestas SFT buenas vs 10 `rejected` de referencia. Debe puntuar más alto las buenas.

## Datos actuales

```
data/dataset_sft.jsonl  (30 ejemplos originales)
data/dataset_dpo.jsonl  (30 pares de referencia)
data/train.jsonl        (27 - tras split)
data/eval.jsonl         (3 - tras split)
data/candidates.jsonl   (5 prompts con 4 candidatos cada uno)
data/dpo.jsonl          (30 pares construidos)
data/eval_prompts.jsonl (30 prompts para evaluación)
```

## DPO con LoRA usando `ref_model=None` (eficiente en RAM)

Este proyecto sigue el enfoque correcto para CPU + LoRA:

- **Un solo modelo:** Se carga `base_model` + adaptador LoRA una sola vez con `PeftModel(..., is_trainable=True)`.
- **Referencia implícita:** Con `ref_model=None`, `DPOTrainer` de TRL desactiva el adaptador LoRA (`disable_adapter()`) para calcular las log-probabilidades del modelo de referencia. **No se carga un segundo modelo completo.**
- **Solo LoRA se entrena:** ~1% de parámetros. Al final se guarda únicamente el adaptador actualizado.
- **Ahorro de RAM:** Ideal para Ryzen 5 + 7 GiB sin CUDA/ROCm.

### Formato del dataset

DPO requiere pares `(prompt, chosen, rejected)`:

```json
{"prompt": "...", "chosen": "...", "rejected": "..."}
```

Tanto `data/dpo.jsonl` (construido con juez local + reglas) como datasets públicos como [`HumanLLMs/Human-Like-DPO-Dataset`](https://huggingface.co/datasets/HumanLLMs/Human-Like-DPO-Dataset) cumplen este formato.

### Implementación en `model/train.py`

```python
from peft import PeftModel
from trl import DPOTrainer, DPOConfig

# Cargar base + adaptador existente (entrenable)
model = AutoModelForCausalLM.from_pretrained(base_model, torch_dtype=torch.float32)
model = PeftModel.from_pretrained(model, lora_path, is_trainable=True)
model.config.use_cache = False

# Dataset
dataset = Dataset.from_list(dpo_data)

# Config
dpo_config = DPOConfig(
    beta=0.1,
    num_train_epochs=1,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8,
    gradient_checkpointing=True,
    learning_rate=5e-7,
    fp16=False,
    bf16=False,
    no_cuda=True,
    dataloader_num_workers=0,
    report_to=[],
)

# CLAVE: ref_model=None
trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=dpo_config,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
trainer.train()
model.save_pretrained(lora_path)  # guardar solo adaptador
```

### Puntos clave
| Concepto | Explicación |
|----------|-------------|
| `ref_model=None` | TRL usa el mismo modelo con el adaptador LoRA apagado como referencia. Sin duplicar el modelo. |
| `is_trainable=True` | El adaptador se sigue entrenando con DPO (continuando desde el SFT). |
| `torch.float32` | Obligatorio en CPU sin bitsandbytes. |
| `gradient_checkpointing=True` | Reduce uso de memoria a costa de tiempo. |
| Guardar solo adaptador | Más ligero. Se puede fusionar con `merge_adapter()` después. |

### Nota sobre datasets
- **Dataset propio (SAMARITAN):** Construido con juez local + reglas deterministas, alineado al tono frío/cortés/declarativo. Recomendado para mantener la personalidad.
- **Dataset público (Human-Like):** Útil para hacerlo más conversacional/natural, pero puede diluir el tono SAMARITAN si se mezcla sin criterio.

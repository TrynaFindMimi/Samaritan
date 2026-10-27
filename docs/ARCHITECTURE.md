# Arquitectura de Capas - SAMARITAN

## Principios
- **Separación estricta:** Cada capa vive en su propio paquete.
- **Comunicación adyacente:** Solo habla con la capa inmediatamente adyacente a través de una interfaz definida.
- **Sin imports hacia arriba:** Ninguna capa importa de una capa superior.
- **Un solo punto de contacto con Ollama:** Únicamente `serving/` conoce Ollama.
- **Tono, no lógica:** La personalidad es solo tono. El código debe ser correcto.

## Diagrama de capas

```
┌─────────────────────────────────────────────────────────┐
│                        UI (ui/)                         │
│  TUI estilo Samaritan - Solo recibe texto filtrado      │
└─────────────────────────────────────────────────────────┘
                          ▲ (texto filtrado)
┌─────────────────────────────────────────────────────────┐
│                      OUTPUT (output/)                    │
│  Filtro final obligatorio - Elimina emojis, normaliza ! │
└─────────────────────────────────────────────────────────┘
                          ▲ (respuesta cruda)
┌─────────────────────────────────────────────────────────┐
│                      AGENT (agent/)                      │
│  Orquestación - Permisos, historial, herramientas       │
└─────────────────────────────────────────────────────────┘
                          ▲
                    ┌─────┴─────┐
                    │  SERVING   │  ← ÚNICA CAPA QUE CONOCE OLLAMA
                    │ (serving/) │
                    └───────────┘
                          │ generate()/unload()
                    ┌─────┴─────────────────────────────────┐
                ┌───▼───┐  ┌─────────┐  ┌─────────────────┐
                │ DATA  │  │  MODEL  │  │     JUDGE       │
                │(data/)│  │(model/) │  │    (judge/)     │
                └───────┘  └─────────┘  └─────────────────┘
```

## Interfaces entre capas

| Capa | Exporta | Usado por | Notas |
|------|---------|-----------|-------|
| `data` | `build_datasets()` | Scripts/main | Lee archivos JSONL, valida, genera train/eval |
| `model` | `train_sft()`, `train_dpo()`, `merge_adapter()`, `export_gguf()` | Scripts/main | Usa transformers/peft/trl. Solo CPU, fp32 |
| `serving` | `generate()`, `unload()`, `create_model()` | agent, judge | Única que llama a Ollama API |
| `judge` | `build_dpo_dataset()` | Scripts/main | Usa solo `serving.generate/unload` |
| `agent` | `SamaritanAgent` | UI/CLI | Usa solo `serving.generate()`, aplica política |
| `output` | `filter_output()`, `validate_format()` | agent, UI | Siempre aplicado |
| `ui` | `SamaritanTUI` | CLI | Solo muestra texto filtrado |

## Reglas de personalidad

- Fría, cortés y declarativa. Frases cortas.
- Cero emojis, cero exclamaciones, cero disculpas.
- Estados: `ANALYZING`, `EXECUTING`, `COMPLETE`, `ANOMALY DETECTED`
- Antes de acciones destructivas: `ACCIÓN`, `IMPACTO`, `AUTHORIZE? [Y/N]`
- Si faltan datos: `DATOS INSUFICIENTES` + lista de lo requerido
- La personalidad es solo tono: el código debe ser correcto

## DPO con LoRA eficiente (referencia implícita)

En `model/train.py`, `train_dpo()` implementa el enfoque eficiente:

1. Se carga **una sola instancia** del modelo base + adaptador LoRA existente.
2. `DPOTrainer` recibe `model_ref=None`. TRL calcula las probabilidades de referencia desactivando temporalmente el adaptador LoRA.
3. Solo se actualizan los pesos del adaptador (~1%).
4. Se guarda únicamente el adaptador actualizado en `model/lora_adapter/`.

Esto cumple con la restricción de RAM (7 GiB) y CPU sin CUDA/ROCm.

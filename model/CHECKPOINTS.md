# Checkpoints históricos

Los directorios `checkpoint-4` a `checkpoint-40` corresponden a una ejecución
DPO anterior y se conservan como archivo histórico.

No deben usarse como evidencia de las corridas actuales de SFT/DPO descritas
en `docs/TRAINING.md`. Por ejemplo, `checkpoint-40/trainer_state.json` registra
10 épocas y 40 pasos, mientras que la corrida DPO inicial documentada en esta
entrega registró 4 pasos.

El adaptador final está en `model/lora_adapter/` y fue reentrenado con SFT/DPO
y desplegado como GGUF F16. Para reproducir la corrida centrada en formato:

```bash
source .venv/bin/activate
python scripts/train_format.py
python main.py create-model
```

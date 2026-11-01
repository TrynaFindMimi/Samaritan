# Despliegue del adaptador LoRA

## Estado actual

El modelo `samaritan` está creado en Ollama con:

```text
FROM qwen2.5:0.5b
```

Es decir, **Qwen2.5-0.5B + el system prompt de SAMARITAN**, sin el adaptador LoRA.

## Por qué no se aplicó el adaptador

Ollama 0.40.12 ya no acepta la instrucción `ADAPTER`:

```text
Error: LoRA adapters are no longer supported
```

Por eso el `Modelfile` no incluye la línea `ADAPTER`. El modelo sigue siendo
funcional, pero no usa el fine-tuning de `model/lora_adapter/`.

## Cómo usar el adaptador más adelante

La ruta soportada es fusionar el adaptador y exportar un GGUF:

```bash
cd /Users/leonardocarrillo/AIProj/Samaritan
source .venv/bin/activate

# 1. Fusionar adaptador + base
python -c "from model.train import merge_adapter; merge_adapter()"

# 2. Convertir a GGUF f16 con llama.cpp
python llama.cpp/convert_hf_to_gguf.py model/merged \
  --outfile model/gguf/samaritan-f16.gguf \
  --outtype f16

# 3. Cuantizar
llama.cpp/build/bin/llama-quantize \
  model/gguf/samaritan-f16.gguf \
  model/gguf/samaritan-q4_K_M.gguf \
  Q4_K_M
```

Después, cambiar el `Modelfile` a:

```text
FROM ./model/gguf/samaritan-q4_K_M.gguf
```

Y recrear:

```bash
python3 main.py create-model
```

## Verificación

```bash
python3 main.py create-model
ollama show samaritan
python3 main.py ask "Analiza el estado del sistema."
```

## Limitación conocida

Hasta que se haga la fusión + GGUF, `samaritan` no refleja el adaptador
entrenado. La personalidad se mantiene por el system prompt.

# Despliegue del adaptador LoRA

## Estado actual

El modelo `samaritan` está creado en Ollama desde un GGUF fusionado:

```text
FROM ../model/gguf/samaritan-f16.gguf
```

Características actuales:

```text
Arquitectura: qwen2
Parámetros:   494.03M
Cuantización: F16
Tamaño:       ~994 MB
```

El adaptador LoRA **sí está incluido**: se fusionó con el modelo base y se convirtió a GGUF.

## Por qué no se usa `ADAPTER`

Ollama 0.40.12 ya no acepta la instrucción `ADAPTER`:

```text
Error: LoRA adapters are no longer supported
```

Por eso la única ruta soportada es fusionar el adaptador y usar un GGUF.

## Cómo se generó

```bash
cd /Users/leonardocarrillo/AIProj/Samaritan
source .venv/bin/activate

# 1. Fusionar adaptador + modelo base
python -c "from model.train import merge_adapter; merge_adapter()"

# 2. Convertir a GGUF F16 con llama.cpp
python ../llama.cpp/convert_hf_to_gguf.py model/merged \
  --outfile model/gguf/samaritan-f16.gguf \
  --outtype f16

# 3. Apuntar el Modelfile al GGUF (ruta relativa a serving/)
# FROM ../model/gguf/samaritan-f16.gguf

# 4. Recrear el modelo
python main.py create-model
```

## Verificación

```bash
ollama show samaritan
ollama list | grep samaritan
python main.py ask "Analiza el estado del sistema."
python main.py query "¿Quién eres?"
```

Debe aparecer `quantization F16` y el modelo debe responder.

## Opcional: cuantizar a Q4_K_M

F16 funciona, pero ocupa ~1 GB. Para reducirlo se necesita `llama-quantize`, que requiere compilar `llama.cpp`:

```bash
brew install cmake
cd /Users/leonardocarrillo/AIProj/llama.cpp
cmake -B build
cmake --build build --config Release
cd /Users/leonardocarrillo/AIProj/Samaritan

/Users/leonardocarrillo/AIProj/llama.cpp/build/bin/llama-quantize \
  model/gguf/samaritan-f16.gguf \
  model/gguf/samaritan-q4_K_M.gguf \
  Q4_K_M
```

Luego cambiar el `Modelfile` a:

```text
FROM ../model/gguf/samaritan-q4_K_M.gguf
```

Y recrear:

```bash
python main.py create-model
```

## Limitaciones

- El GGUF F16 ocupa ~1 GB y Ollama lo carga completo.
- El adaptador fusionado no garantiza que el modelo 0.5B cumpla el formato `ANALYZING ... COMPLETE`; eso depende también del prompt y del entrenamiento.
- Si se reentrena el adaptador, hay que repetir la fusión y la conversión a GGUF.

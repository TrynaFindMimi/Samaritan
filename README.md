# SAMARITAN

Agente local offline sobre `qwen2.5:0.5b` con Ollama y una interfaz de terminal.
Todo corre en local: sin APIs externas, sin nube y sin datos que salgan del equipo.

## Inicio rapido

```bash
# 1. Dependencias de Python (solo para la CLI y el filtro)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Base + modelo samaritan en Ollama
./serving/create_model.sh

# 3. Usar
python main.py
```

`create_model.sh` hace tres cosas: descarga `qwen2.5:0.5b`, elimina el modelo
`samaritan` anterior y lo vuelve a crear con el system prompt de
`serving/Modelfile`.

## Uso

```bash
python main.py                    # modo interactivo
python main.py query "consulta"   # agente + filtro
python main.py ask "consulta"     # modelo directo + filtro
python main.py eval               # evaluacion
```

Para salir del modo interactivo: `exit`, `salir`, `quit` o `q`.

## Como funciona

```
usuario -> main.py -> agent/ -> serving/ (Ollama) -> output/ -> ui/
```

| Capa | Directorio | Funcion |
|---|---|---|
| Datos | `data/` | Limpieza y validacion de datasets |
| Modelo | `model/` | Entrenamiento LoRA opcional (SFT/DPO) |
| Serving | `serving/` | Unica capa que habla con Ollama |
| Juez | `judge/` | Generacion opcional de pares DPO |
| Agente | `agent/` | Historial, permisos y acciones destructivas |
| Salida | `output/` | Filtro obligatorio de todas las respuestas |
| UI | `ui/` | Interfaz de terminal |

El modelo por defecto es la base `qwen2.5:0.5b` con el system prompt del
Modelfile. No hace falta entrenar para usarlo.

## Reglas de respuesta

- Sin emojis, sin signos de exclamacion, sin disculpas.
- Frases cortas y solo la informacion necesaria.
- Toda respuesta termina con `COMPLETE`.
- Ante una accion destructiva:

```
ACCION: <descripcion>
IMPACTO: <riesgo>
AUTHORIZE? [Y/N]
```

- Si falta informacion:

```
DATOS INSUFICIENTES
REQUERIDO:
  - <dato 1>
  - <dato 2>
```

`output/filter_output()` se aplica siempre: elimina emojis, cambia `!` por `.`
y quita `¡`, aunque el modelo falle.

## Configuracion

Todo esta en `config.yaml`:

| Seccion | Contenido |
|---|---|
| `project` | Nombre y version |
| `hardware` | Limites de RAM y dispositivo |
| `model` | Modelo base, longitud y LoRA |
| `training` | Parametros de SFT y DPO |
| `ollama` | Host y modelos de generacion/juez |
| `judge` | Reglas de puntuacion DPO |
| `data` | Rutas de datasets |
| `paths` | Salidas de entrenamiento |

## Entrenamiento opcional

El flujo SFT/DPO existe pero no es necesario para usar el agente. Requiere CPU,
RAM y tiempo; esta pensado para ajustar el estilo del modelo.

```bash
python main.py build-data    # genera data/train.jsonl y data/eval.jsonl
python main.py train-sft     # LoRA SFT
python main.py create-model  # recrea samaritan en Ollama
python main.py build-dpo     # pares DPO con juez local
python main.py train-dpo     # LoRA DPO
```

Detalles en [docs/TRAINING.md](docs/TRAINING.md).

## Requisitos

- Python 3.10 o superior
- Ollama en `http://localhost:11434`
- CPU con suficiencia para `qwen2.5:0.5b` (sin CUDA ni ROCm)
- Dependencias en `requirements.txt`

## Estructura

```
Samaritan/
├── agent/          Agente y politica de seguridad
├── data/           Datasets y validadores
├── docs/           Documentacion
├── judge/          Juez offline para DPO
├── model/          Entrenamiento LoRA (opcional)
├── output/         Filtro obligatorio de salida
├── serving/        Cliente Ollama y Modelfile
├── tests/          Tests
├── ui/             Interfaz de terminal
├── config.yaml     Configuracion
├── main.py         Entrada CLI
└── README.md
```

## Documentacion

- [QUICKSTART.md](docs/QUICKSTART.md)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [TRAINING.md](docs/TRAINING.md)
- [EVALUATION.md](docs/EVALUATION.md)
- [FILEMAP.md](docs/FILEMAP.md)

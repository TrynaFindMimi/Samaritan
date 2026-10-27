# SAMARITAN

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                                                              ┃
┃                        ▓▓▓   S A M A R I T A N   ▓▓▓                          ┃
┃                                                                              ┃
┃                  AGENTE LOCAL OFFLINE | SFT + DPO | OLLAMA                  ┃
┃                                                                              ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

Sistema de agente local offline con entrenamiento LoRA (SFT + DPO) sobre `Qwen2.5-0.5B-Instruct`, serving vía Ollama y una interfaz TUI al estilo operativo. Todo corre 100% local sin dependencias de APIs externas.

## Diagrama General

```mermaid
graph TD
    A["📊 DATA\nbuild-datasets"] --> B["🧠 MODEL - SFT\nLoRA Training"]
    B --> C["🔗 MERGE + GGUF\nAdapter Fusion"]
    C --> D["🦙 SERVING\nOllama Model"]
    D --> E["⚖️ JUDGE - DPO\nAuto-generation"]
    E --> F["🎯 MODEL - DPO\nPreference Training"]
    F --> G["🔗 MERGE + GGUF\nRe-fusion"]
    G --> H["🦙 SERVING\nUpdate samaritan"]
    H --> I["🤖 AGENT\nSamaritanAgent"]
    I --> J["🛡️ OUTPUT FILTER\nMandatory Post-Process"]
    J --> K["💻 UI - TUI\nTerminal Interface"]
    
    style A fill:#2d5aa0,stroke:#fff,color:#fff
    style B fill:#d35400,stroke:#fff,color:#fff
    style C fill:#e67e22,stroke:#fff,color:#fff
    style D fill:#27ae60,stroke:#fff,color:#fff
    style E fill:#8e44ad,stroke:#fff,color:#fff
    style F fill:#d35400,stroke:#fff,color:#fff
    style G fill:#e67e22,stroke:#fff,color:#fff
    style H fill:#27ae60,stroke:#fff,color:#fff
    style I fill:#c0392b,stroke:#fff,color:#fff
    style J fill:#f39c12,stroke:#fff,color:#fff
    style K fill:#34495e,stroke:#fff,color:#fff
```

## Arquitectura por Capas

```mermaid
flowchart LR
    subgraph Capas["ARQUITECTURA DE CAPAS"]
        D["data/\nValidación & Datasets"]
        M["model/\nLoRA SFT/DPO"]
        S["serving/\nOllama Client"]
        J["judge/\nAuto DPO Builder"]
        A["agent/\nOrquestación"]
        O["output/\nFiltro Obligatorio"]
        U["ui/\nTUI Interface"]
    end
    
    D --> M
    M --> S
    S --> J
    J --> M
    A --> S
    A --> O
    O --> U
    
    style D fill:#3498db,stroke:#fff,color:#fff
    style M fill:#e74c3c,stroke:#fff,color:#fff
    style S fill:#2ecc71,stroke:#fff,color:#fff
    style J fill:#9b59b6,stroke:#fff,color:#fff
    style A fill:#e67e22,stroke:#fff,color:#fff
    style O fill:#f1c40f,stroke:#000,color:#000
    style U fill:#1abc9c,stroke:#fff,color:#fff
```

| Capa | Directorio | Propósito | Archivos clave |
|---|---|---|---|
| **Datos** | `data/` | Generación, validación y limpieza de datasets para entrenamiento SFT y DPO. | `dataset.py`, `validators.py` |
| **Modelo** | `model/` | Entrenamiento LoRA (SFT/DPO), fusión de adaptador y exportación a GGUF. | `train.py` |
| **Serving** | `serving/` | Única capa que interactúa con Ollama. Generación, creación de modelos y descarga de VRAM. | `ollama_client.py`, `Modelfile`, `create_model.sh` |
| **Juez (DPO)** | `judge/` | Generación automática de pares preferidos/rechazados con juez local sin anotación manual. | `dpo_builder.py`, `rules.py` |
| **Agente** | `agent/` | Lógica del agente SAMARITAN (orquestación). Reconoce jerarquía `ADMIN`. | `agent.py` |
| **Salida** | `output/` | Filtro obligatorio de post-procesado. Garantiza formato y cumplimiento de reglas. | `filter.py` |
| **UI** | `ui/` | Interfaz TUI en modo operativo (texto palabra por palabra, estilo terminal). | `tui.py` |
| **Utilidades** | Raíz | Configuración, chequeo de RAM, helpers comunes. | `config.yaml`, `utils.py` |

### Detalle por capa

#### `data/` - Capa de datos
- **Función:** `build_datasets()` lee `dataset_sft.jsonl` y `dataset_dpo.jsonl` desde `data/`, aplica filtros y genera `train.jsonl` y `eval.jsonl`.
- **Validadores (`validators.py`):** Detecta emojis, signos de exclamación (`!`, `¡`), bloques de código Python, valida con `ast.parse`, normaliza y limpia texto.
- **Filtros:** Elimina contenido no permitido antes del entrenamiento.

#### `model/` - Capa de modelo
- **Modelo base:** `Qwen/Qwen2.5-0.5B-Instruct`
- **LoRA:** `r=16`, `alpha=32`, `dropout=0.05`. Módulos objetivo configurables en `config.yaml`. Soporta entrenar solo las últimas N capas (`layers_to_transform`).
- **Entrenamiento:** `max_seq_length=512`, batch size 1, gradient accumulation 8, gradient checkpointing, fp32 (sin bitsandbytes), optimizado para CPU.
- **Funciones:** `train_sft()`, `train_dpo()`, `merge_adapter()`, `export_gguf()`

```mermaid
graph LR
    A[Base Model\nQwen2.5-0.5B] --> B[LoRA Adapter\nr=16, alpha=32]
    B --> C[Merge\nLoraModel.merge_and_unload]
    C --> D[GGUF Export\nllama.cpp]
    
    style A fill:#3498db,stroke:#fff,color:#fff
    style B fill:#e74c3c,stroke:#fff,color:#fff
    style C fill:#f39c12,stroke:#fff,color:#fff
    style D fill:#2ecc71,stroke:#fff,color:#fff
```

#### `serving/` - Capa de serving
- **Única con acceso a Ollama:** `generate(messages, model=None, options=None)` hace `POST` a `http://localhost:11434/api/chat`. `unload(model)` libera el modelo de RAM. `create_model(name, modelfile)` crea el modelo desde un Modelfile.
- **Modelfile:** Define el system prompt de SAMARITAN con protocolo de seguridad, reconocimiento `ADMIN` y parámetros `temperature=0.3`, `top_p=0.9`, `repeat_penalty=1.1`. `create_model.sh` ejecuta `ollama create samaritan -f Modelfile`.

#### `judge/` - Capa de juez offline
Genera pares DPO automáticamente mediante un juez local:

```mermaid
flowchart TD
    A[Prompts desde train.jsonl] --> B[Generar 4 candidatos\nsamaritan temp=0.9]
    B --> C[Descargar generador\nunload]
    C --> D[Puntuar con juez\nqwen2.5:3b temp=0]
    D --> E[Aplicar reglas automáticas\nemojis, !, código, formato]
    E --> F{Diferencia >= 2\nchosen >= 6?}
    F -->|SI| G[Crear par DPO\nchosen vs rejected]
    F -->|NO| H[Descartar]
    G --> I[Mezclar con pares referencia]
    I --> J[Generar dpo.jsonl\nReporte + Calibración]
    
    style A fill:#3498db,stroke:#fff,color:#fff
    style B fill:#2ecc71,stroke:#fff,color:#fff
    style C fill:#e74c3c,stroke:#fff,color:#fff
    style D fill:#9b59b6,stroke:#fff,color:#fff
    style E fill:#f39c12,stroke:#fff,color:#fff
    style F fill:#34495e,stroke:#fff,color:#fff
    style G fill:#27ae60,stroke:#fff,color:#fff
    style H fill:#c0392b,stroke:#fff,color:#fff
    style J fill:#1abc9c,stroke:#fff,color:#fff
```

1. **A) Candidatos:** Para cada prompt en `train.jsonl` genera 4 respuestas con el modelo generador (por defecto `samaritan`) a `temperature=0.9`. Guarda incrementalmente en `candidates.jsonl`.
2. **B) Puntuación:** Usa un juez distinto (por defecto `qwen2.5:3b`), `temperature=0`, semilla fija. Descarga el generador con `unload()` antes de cargar el juez. Solicita JSON estricto `{puntaje, motivo}` con reintentos.
3. **C) Reglas automáticas:** Ajustes deterministas - descartar emojis/signos de exclamación, penalizar código Python inválido, require estado inicial en mayúsculas, exigir `AUTHORIZE? [Y/N]` en acciones destructivas, penalizar respuestas excessively largas.
4. **D) Pares DPO:** Selecciona `chosen` (mayor puntaje) vs `rejected` (menor). Se descarta si diferencia < 2 o `chosen < 6`. Se mezclan con pares de referencia. Genera muestra aleatoria de 20 pares, reporte y calibración.

#### `output/` - Capa de salida (obligatoria)
Siempre se aplica tras cualquier respuesta.

```mermaid
flowchart LR
    A[Respuesta Raw] --> B[filter_output]
    B --> C[Elimina emojis]
    C --> D[Reemplaza ! por .]
    D --> E[Elimina ¡]
    E --> F[validate_format]
    F --> G{Estado inicial\nmayúsculas + COMPLETE?}
    G -->|SI| H[Respuesta Filtrada OK]
    G -->|NO| I[Aplicar correcciones]
    I --> H
    
    style A fill:#e74c3c,stroke:#fff,color:#fff
    style B fill:#f39c12,stroke:#fff,color:#fff
    style F fill:#9b59b6,stroke:#fff,color:#fff
    style H fill:#2ecc71,stroke:#fff,color:#fff
    style I fill:#e67e22,stroke:#fff,color:#fff
```

- **`filter_output()`:** Elimina emojis, reemplaza `!` por `.`, elimina `¡`.
- **`validate_format()`:** Verifica estado inicial en mayúsculas y presencia de `COMPLETE`.

#### `ui/` - Capa de interfaz
TUI al estilo SAMARITAN: fondo negro, texto blanco hueso, rojo solo para alertas, tipografía monoespaciada, aparición palabra por palabra, indicador `►`. Solo recibe texto ya filtrado desde `output/`.

#### `agent/` - Capa de agente
Orquesta el flujo de consulta usando el modelo `samaritan` vía `serving/`. Incluye protección contra comandos prohibidos, detección de acciones destructivas y reconocimiento de `ADMIN` con acceso privilegiado.

```mermaid
flowchart TD
    A[Mensaje Usuario] --> B{Identifica ADMIN?}
    B -->|SI| C[ACCESS GRANTED :: ADMIN]
    B -->|NO| D{Comando prohibido?}
    D -->|SI| E[ANOMALY DETECTED\nCOMANDO PROHIBIDO\nCOMPLETE]
    D -->|NO| F{Acción destructiva?}
    F -->|SI| G[ACCIÓN + IMPACTO\nAUTHORIZE? Y/N]
    F -->|NO| H[Generar con samaritan]
    H --> I[Aplicar filtro_output]
    C --> I
    G --> I
    I --> J[Respuesta Filtrada]
    
    style A fill:#3498db,stroke:#fff,color:#fff
    style B fill:#9b59b6,stroke:#fff,color:#fff
    style C fill:#2ecc71,stroke:#fff,color:#fff
    style D fill:#e74c3c,stroke:#fff,color:#fff
    style E fill:#c0392b,stroke:#fff,color:#fff
    style F fill:#e67e22,stroke:#fff,color:#fff
    style G fill:#f39c12,stroke:#fff,color:#fff
    style H fill:#1abc9c,stroke:#fff,color:#fff
    style J fill:#27ae60,stroke:#fff,color:#fff
```

## Flujo de Ejecución Completo

```mermaid
sequenceDiagram
    participant U as Usuario
    participant M as main.py
    participant D as data/
    participant ML as model/
    participant S as serving/
    participant J as judge/
    participant A as agent/
    participant O as output/
    participant UI as ui/
    
    U->>M: build-data
    M->>D: build_datasets()
    D-->>M: train.jsonl, eval.jsonl
    
    U->>M: train-sft
    M->>ML: train_sft() → merge_adapter() → export_gguf()
    ML-->>S: adapter fusionado
    
    U->>M: create-model
    M->>S: create_model('samaritan', Modelfile)
    S-->>Ollama: modelo samaritan creado
    
    U->>M: build-dpo
    M->>J: build_dpo_dataset()
    J->>S: generate candidatos (4x)
    J->>S: unload + juez scoring
    J-->>M: dpo.jsonl
    
    U->>M: train-dpo
    M->>ML: train_dpo() → merge_adapter() → export_gguf()
    ML-->>S: re-exportar modelo
    
    U->>M: query/ask o interactivo
    M->>A: process()
    A->>S: generate()
    S-->>A: respuesta raw
    A->>O: filter_output()
    O-->>UI: texto filtrado
    UI-->>U: visualización TUI
```

## Uso

### Modo interactivo
```bash
python main.py
```
Muestra `ANALYZING`, `SAMARITAN`, `COMPLETE` y entra en bucle interactivo. Salir con `exit`, `salir`, `quit`, `q`.

### Consulta con TUI
```bash
python main.py query "tu consulta"
```
Procesa con el agente, filtra la salida y la muestra con la TUI.

### Consulta directa
```bash
python main.py ask "tu consulta"
```
Genera directamente con el modelo `samaritan` vía Ollama, filtra y muestra por stdout.

### Evaluación
```bash
python main.py eval
```

## Configuración

Toda la configuración se centraliza en `config.yaml`. Secciones principales: `project`, `hardware`, `model`, `training` (sft/dpo), `ollama`, `judge`, `data`, `paths`.

```mermaid
graph TD
    A[config.yaml] --> B[hardware\nCPU-only, 7GB RAM]
    A --> C[model\nQwen2.5-0.5B + LoRA]
    A --> D[training\nSFT/DPO params]
    A --> E[ollama\nhost + models]
    A --> F[judge\nscoring rules]
    A --> G[data\npaths]
    A --> H[paths\noutputs]
    
    style A fill:#34495e,stroke:#fff,color:#fff
    style B fill:#e74c3c,stroke:#fff,color:#fff
    style C fill:#3498db,stroke:#fff,color:#fff
    style D fill:#e67e22,stroke:#fff,color:#fff
    style E fill:#2ecc71,stroke:#fff,color:#fff
    style F fill:#9b59b6,stroke:#fff,color:#fff
    style G fill:#1abc9c,stroke:#fff,color:#fff
    style H fill:#f39c12,stroke:#fff,color:#fff
```

Ver `config.yaml` para detalles de parámetros (LoRA, batch, learning rates, seeds, umbrales del juez, etc.).

## Requisitos

- **Python:** 3.10+
- **Ollama:** Corriendo localmente en `http://localhost:11434`
- **Hardware objetivo:** AMD Ryzen 5 5500U (CPU-only), sin CUDA/ROCm, ~7 GiB RAM
- **Dependencias:** Ver `requirements.txt`
- **Entrenamiento:** fp32 sin bitsandbytes, optimizado para CPU with gradient checkpointing

## Instalación

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Instalar dependencias
pip install -r requirements.txt

# Asegurar Ollama corriendo y tener modelos necesarios
ollama pull qwen2.5:3b  # juez (recomendado >= tamaño del generador)
```

## Estructura del repositorio

```mermaid
mindmap
  root((SAMARITAN))
    agent
      agent.py
    data
      dataset.py
      validators.py
    judge
      dpo_builder.py
      rules.py
    model
      train.py
    serving
      ollama_client.py
      Modelfile
    output
      filter.py
    ui
      tui.py
    tests
    docs
      ARCHITECTURE.md
      TRAINING.md
      FILEMAP.md
```

```
Samaritan/
├── agent/          # Lógica del agente (reconoce ADMIN)
├── data/           # Datasets y validadores
├── docs/           # Documentación + gráficas
├── judge/          # Juez offline para DPO
├── model/          # Entrenamiento LoRA, fusión, GGUF
├── output/         # Filtro obligatorio de salida
├── serving/        # Cliente Ollama y Modelfile
├── tests/          # Tests unitarios
├── ui/             # Interfaz TUI
├── chat.py         # Utilidades de chat
├── config.yaml     # Configuración central
├── eval.py         # Evaluación
├── main.py         # Punto de entrada CLI
├── requirements.txt
├── utils.py        # Utilidades comunes
└── README.md
```

## Documentación Adicional

- [**ARCHITECTURE.md**](docs/ARCHITECTURE.md) - Arquitectura detallada del sistema
- [**TRAINING.md**](docs/TRAINING.md) - Guía completa de entrenamiento SFT + DPO
- [**EVALUATION.md**](docs/EVALUATION.md) - Guía de evaluación
- [**QUICKSTART.md**](docs/QUICKSTART.md) - Guía rápida de inicio
- [**FILEMAP.md**](docs/FILEMAP.md) - Mapa detallado de archivos

## Notas

- Todo el procesamiento es **100% local y offline**.
- Solo `serving/` conoce Ollama; el resto de capas son agnósticas al backend.
- El filtro de salida (`output/filter.py`) es **obligatorio** y se aplica en todos los caminos de respuesta.
- Protocolo de seguridad estricto con reconocimiento de jerarquía **ADMIN**.
- En algunas instalaciones se ha reutilizado un adaptador preexistente en `the-machine-v3/models/samaritan/`.
```
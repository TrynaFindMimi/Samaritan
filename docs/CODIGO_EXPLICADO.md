# SAMARITAN — el código explicado

Documento para **entender y memorizar el código real**, no para leerlo en voz alta.
Cada afirmación está anclada a `archivo:línea` del estado actual del repo.

---

## 0. El repo en una imagen

```
                    config.yaml  ──────────────┐
                                                │  (todo módulo hace:
                                                │   cfg = config or load_config())
                                                ▼
  main.py ──► data/dataset.py ──► data/train.jsonl ──► model/train.py (SFT)
     │              │                                        │
     │              └──► data/eval.jsonl                     ▼
     │                                              model/lora_adapter
     │                                                       │
     │                        judge/dpo_builder.py ◄─────────┘
     │                                 │
     │                                 ▼
     │                          data/dpo.jsonl ──► model/train.py (DPO)
     │                                                       │
     │                                        merge_adapter + export_gguf
     │                                                       ▼
     │                                            model/gguf/*.gguf
     │                                                       │
     ▼                                                       ▼
  main.py query ──► agent/agent.py ──► serving/ollama_client.py ──► Ollama
                          │                                             │
                          ▼                                             │
                  output/filter.py ◄────────────────────────────────────┘
                          │
                          ▼
                     ui/tui.py
```

**Regla general del repo:** ningún módulo importa `torch`/`transformers` en la cabecera.
Se importan *dentro* de la función que los usa (`model/train.py:22-34`, `:161-166`, `:248-255`).
Eso permite ejecutar `main.py query` sin tener el stack de entrenamiento instalado.

---

## 1. Las tres cadenas de ejecución que hay que saber de memoria

### A. Una consulta (lo que ocurre al escribir en la TUI)

```
main.py:87   main()            ← sin argumentos entra en modo interactivo
main.py:94   tui.boot()
main.py:106  agent.process(user_input)
  agent/agent.py:59            history.append(user)
  agent/agent.py:63            check_command()  → lista FORBIDDEN_COMMANDS
  agent/agent.py:69            _is_destructive() → lista DESTRUCTIVE_PATTERNS
  agent/agent.py:76            generate(messages)
    serving/ollama_client.py:30  requests.post(host + "/api/chat")
    serving/ollama_client.py:33  return data["message"]["content"]
  agent/agent.py:79            finalize_output(raw)
main.py:107  finalize_output(resp)   ← se aplica DOS veces (idempotente)
main.py:108  tui.respond(filtered)
```

**Frase para defender:** *"el filtro se aplica dos veces: dentro del agente y en la CLI. Es idempotente, así que no hay doble efecto."*

### B. Construcción de datos y SFT

```
main.py:7    cmd_build_data
  data/dataset.py:34  build_datasets()
  data/dataset.py:44  load_jsonl(input_sft)
  data/dataset.py:53  is_valid_sft_example()   ← validators.py:50
  data/dataset.py:60  clean_text()             ← validators.py:71
  data/dataset.py:75  random.seed(42)
  data/dataset.py:84  save_jsonl(train) / (eval)

main.py:14   cmd_train_sft
  model/train.py:19   train_sft()
  model/train.py:63   LoraConfig(r=16, alpha=32, dropout=0.05, 7 módulos)
  model/train.py:86   format_example()  → apply_chat_template
  model/train.py:103  tokenize_fn()     → max_length=512, truncation
  model/train.py:148  trainer.train()
  model/train.py:152  save_pretrained(model/lora_adapter)
  model/train.py:158  merge_adapter()
  model/train.py:190  export_gguf()
```

### C. Construcción del DPO (el flujo más "de paper")

```
main.py:31   cmd_build_dpo
  judge/dpo_builder.py:96   build_dpo_dataset()
  ── ETAPA A ──  :126-142   4 candidatos por prompt, temperature=0.9
  ── descarga ── :144-146   unload(generator) + sleep(2)
  ── ETAPA B/C ─ :148-171   judge_score() + apply_rules()  → scored.jsonl
  ── ETAPA D ──  :173-195   chosen = max(final_score), rejected = min(...)
                            exige diff >= 2 y chosen >= 6
  ── referencia ─ :197-207  añade dataset_dpo.jsonl tal cual
  ── salida ──   :210       data/dpo.jsonl
```

Ese `unload` + `sleep(2)` existe porque el juez (`qwen2.5:3b`) y el generador (`samaritan`) no caben juntos en RAM. **Es la evidencia de que el flujo está pensado para hardware modesto.**

---

## 2. Archivo por archivo

### `config.yaml` — la única fuente de verdad

Todos los módulos repiten el patrón `cfg = config or load_config()`. Valores que hay que tener en la cabeza:

| Bloque | Clave | Valor | Quién lo lee |
|---|---|---|---|
| `hardware` | `warn_ram_gib` | 5.5 | `utils.py:70` |
| `model` | `base_model` | `Qwen/Qwen2.5-0.5B-Instruct` | `train.py:41,170,262` |
| `model.lora` | `r / alpha / dropout` | 16 / 32 / 0.05 | `train.py:63-71` |
| `training.sft` | `lr / epochs / batch × accum` | 2e-4 / 1 / 1×8 | `train.py:123-139` |
| `training.dpo` | `beta / lr` | 0.1 / 5e-7 | `train.py:297-303` |
| `ollama` | `host / base / generator / judge` | localhost:11434 / qwen2.5:0.5b / samaritan / qwen2.5:3b | `ollama_client.py:11,22` |
| `judge` | `num_candidates / temp / min_diff / min_chosen` | 4 / 0.9 / 2 / 6 | `dpo_builder.py:105-106,189-192` |
| `data` | `eval_prompts_count` | 30 | `dataset.py:42`, `eval.py:157` |
| `paths` | `lora_adapter / merged / gguf` | `model/lora_adapter`, `model/merged`, `model/gguf` | `train.py:150,172,194` |

### `utils.py` — 79 líneas, 3 ideas

1. **`load_config` (`:9`)** — `ROOT` se calcula desde `__file__`, así que la config se encuentra sin importar el `cwd`.
2. **`get_ram_gib` (`:59`)** — cadena de *fallbacks*: `psutil` → `/proc/meminfo` → `vm_stat` (macOS). Devuelve `None` si no puede, y eso no rompe nada.
3. **`check_ram_before` (`:68`)** — solo **avisa**, no bloquea. Está en `main.py` antes de cada etapa costosa.

> Detalle defendible: es el único punto del repo que asume algo del sistema operativo, y lo hace con tres caminos distintos.

### `data/validators.py` — las reglas, en pequeño

| Función | Línea | Qué hace | Por qué importa |
|---|---|---|---|
| `has_emoji` | `:5` | regex de rangos Unicode | filtra datos antes de entrenar |
| `contains_exclamation` | `:20` | `'!' in s or '¡' in s` | el contrato prohíbe exclamaciones |
| `contains_python_code_block` | `:24` | busca ```` ``` ```` o `def/class/import/from` al inicio de línea | decide si hay que validar sintaxis |
| `python_code_passes_ast` | `:32` | `ast.parse` de cada bloque | validación real, no heurística |
| `is_valid_sft_example` | `:50` | acepta `messages` **o** `prompt`+`response`, y aplica las 3 reglas | es el portero del dataset |
| `clean_text` | `:71` | quita emojis y `¡`, y `!` → `.` salvo `!=` | **la línea `:86` es la clave** |

La línea que hay que citar:

```python
s = re.sub(r'!(?!=)', '.', s)   # validators.py:86
```

`(?!=)` es *negative lookahead*: convierte `!` en `.` solo si **no** va seguido de `=`. Sin eso, `a != b` se rompe y el código generado deja de compilar.

### `data/dataset.py` — de 30 ejemplos a 27/3

- `load_jsonl` (`:11`) **ignora líneas corruptas con `try/except`** en vez de abortar. Mismo patrón repetido en `dpo_builder.py:21` y `eval.py:22` (tres copias del mismo helper; buen candidato a refactor).
- `build_datasets` (`:34`): filtra → limpia → `random.seed(42)` (`:75`) → baraja → parte.
- `:80` — `eval_count = min(eval_count, max(1, len(filtered)//10))`. Con 30 ejemplos: `min(30, 3) = 3`. **De ahí salen los 27/3 del informe.** No está hardcodeado: es el 10 %.
- Si no hay fichero en la ruta configurada, prueba `data/sft.jsonl` y `dataset_sft.jsonl` (`:46`).

### `output/filter.py` — el módulo que garantiza el contrato

Es el archivo más importante para defender el sistema. Cuatro piezas:

1. **`VALID_STATES` (`:5`)** — 10 estados, incluidos `COMPLETE`, `DATOS INSUFICIENTES`, `ACCESS GRANTED/DENIED`.
2. **`_CODE_SEGMENT_RE` (`:20`)** — `r'(```[\s\S]*?```|`[^`\n]*`)'`. El grupo de captura hace que `re.split` devuelva `[prosa, código, prosa, código, ...]`.
3. **`filter_output` (`:34`)** — recorre esas partes y **limpia solo los índices pares** (prosa). El código queda byte a byte igual.
4. **`finalize_output` (`:66`)** — tres pasos:

```python
cleaned = filter_output(text).strip()
if not cleaned: return "ANALYZING\nCOMPLETE"              # :74
if not startswith(VALID_STATES): cleaned = f"{state}\n{cleaned}"  # :76-80
if not _COMPLETE_RE.search(...): cleaned = f"{cleaned}\nCOMPLETE" # :82-83
```

Detalles que demuestran lectura fina:
- `:78` — si el texto empieza por `ACCIÓN`, el estado forzado es `EXECUTING`, no `ANALYZING`. Es una regla semántica escondida en el filtro.
- `validate_format` (`:55`) valida **sobre prosa**, con `\bCOMPLETE\b[.!?]*\s*$` (`:21`), así que un `COMPLETE` dentro de un bloque de código no cuenta.
- **Caso límite real:** `:61` usa `startswith(state)`. `"ANALYZINGLY ... COMPLETE"` pasa la validación. Está reconocido en el informe (§2.10.5) y en trabajo futuro.

### `agent/agent.py` — el "guardián" que no es un guardián

| Elemento | Línea | Idea |
|---|---|---|
| `FORBIDDEN_COMMANDS` | `:8` | 8 patrones regex (`rm -rf /`, `mkfs.`, `dd if=`, `shutdown`...) |
| `DESTRUCTIVE_PATTERNS` | `:21` | 7 patrones que **piden autorización** en vez de bloquear |
| `MAX_HISTORY_MESSAGES` | `:31` | 40 mensajes |
| `check_command` | `:40` | `True` = permitido. Si coincide, el modelo **ni se llama** (`:63`) |
| `_trim_history` | `:50` | recorta al final y luego quita los mensajes iniciales que no sean `user` (`:55`) |
| `process` | `:58` | añade → comprueba → detecta → genera → filtra → guarda |
| `execute_command` | `:87` | simula ejecución; **no ejecuta nada** |

Dos decisiones de regex que hay que saber explicar:
- `\b` en `\bformat\b` y `\bdd\s+if=` (`:26-27`) evita falsos positivos con *"formato"* y *"add "*.
  
  ```python
  r'\bformat\b'    # coincide con "format", no con "formato"
  r'\bdd\s+if='    # exige frontera antes de "dd"
  ```
  
  Hay tests exactos para esto: `tests/test_agent.py:12` (`"formato de informe"` no es destructivo) y `tests/test_agent.py:8` (`"add 2+2"` tampoco).
- `execute_command` y la rama destructiva devuelven texto con `AUTHORIZE? [Y/N]`, pero **nadie lee la respuesta**. La autorización es decorativa.

### `serving/ollama_client.py` — una sola puerta a Ollama

- `generate` (`:14`): payload mínimo `{model, messages, stream: False}`; `timeout=600` (`:30`); devuelve `data["message"]["content"]` o `""` (`:33`).
- `unload` (`:36`): manda `keep_alive: 0`. Si `/api/generate` falla, reintenta por `/api/chat` con `messages: []` (`:47`). **Es el truco para liberar RAM antes de cargar el juez.**
- `create_model` (`:53`): usa `subprocess` con el CLI `ollama create -f Modelfile` **en vez de la API**. El motivo está en el docstring (`:56-58`): `/api/create` cambió y ahora espera `from`/`files`; el CLI sigue aceptando el Modelfile completo y soporta `ADAPTER`.

### `model/train.py` — 334 líneas, 4 funciones

**`train_sft` (`:19`)**
- `:50-56` — carga en `float32` y fuerza `.to("cpu")`; `use_cache = False` (`:57`) porque `gradient_checkpointing` es incompatible con caché.
- `:63-72` — LoRA sobre 7 módulos; `layers_to_transform=None` significa **todas las capas**.
- `:86-98` — `format_example` convierte `messages` o `prompt/response` a un único campo `text` con `apply_chat_template`.
- `:111-121` — **`warmup_ratio` ya no existe en Transformers moderno**, así que calculan `warmup_steps` a mano:

  ```python
  steps_per_epoch = len(tokenized) // (batch * accum)
  warmup_steps = int(total_steps * warmup_ratio)
  ```
  Con 27 ejemplos y `batch × accum = 8`: `27 // 8 = 3` pasos por época. Ojo, `docs/TRAINING.md` registra 4 pasos para la corrida de 1 época y 20 para la de 5 épocas, que no salen exactos de esa fórmula. Si te preguntan: **la fórmula es la del código; las cifras son las que reportó el `Trainer` en cada corrida.** No inventes el redondeo.
- `:141` — `DataCollatorForLanguageModeling(mlm=False)` entrena la secuencia completa, **sin enmascarar el prompt**. Es una decisión simple, y una limitación real: el modelo también aprende a predecir el enunciado del usuario.

**`merge_adapter` (`:158`)** — carga base + `PeftModel.from_pretrained` (`:181`) y `merge_and_unload()` (`:182`): los pesos LoRA se suman a los base y el adaptador desaparece. Guarda en `model/merged`.

**`export_gguf` (`:190`)** — busca `convert_hf_to_gguf.py` en 4 rutas conocidas (`:200-205`), exporta `samaritan-f16.gguf` (`:213`) y, si encuentra `llama-quantize`, genera además Q4_K_M (`:229-235`). Si no encuentra nada, **imprime el motivo y devuelve el directorio** en vez de lanzar excepción (`:239-242`).

**`train_dpo` (`:245`)** — tres detalles que valen oro en una defensa:
- `:273` — `PeftModel.from_pretrained(..., is_trainable=True)`. Sin eso, PEFT carga el adaptador congelado y **DPO no actualiza nada**.
- `:277-283` — guarda explícita: si `trainable_params == 0`, lanza `RuntimeError`. Es una defensa contra el fallo silencioso anterior.
- `:313-327` — `ref_model=None` (TRL usa como referencia el mismo modelo con el adaptador desactivado) y detección por `inspect.signature` del nombre del argumento (`tokenizer` vs `processing_class`) para sobrevivir a cambios de API de TRL.

**Y lo más importante para el informe:** `train_sft` guarda en `model/lora_adapter` (`:152`) y `train_dpo` guarda en **la misma ruta** (`:331`). No hay snapshots por etapa. Eso es exactamente el límite nº 1 del informe, y está a la vista en una línea.

### `judge/dpo_builder.py` — generación → puntuación → pares

- `JUDGE_PROMPT` (`:35`) — 3 criterios ponderados 4/3/3 (tono, limpieza, utilidad) y salida JSON `{"puntaje": n, "motivo": "..."}`.
- `judge_score` (`:44`) — `temperature=0`, `seed=1234`, hasta `max_retries+1` intentos. Extrae el JSON con `find('{')` / `rfind('}')` (`:53-57`) porque el modelo suele envolverlo en texto; luego **recorta a `[0, 10]`** (`:59`).
- `apply_rules` (`:67`) — devuelve `(ajuste, razones)`:

  | Regla | Ajuste |
  |---|---|
  | emoji o exclamación | `0` + `descartar...` (señal de descarte total) |
  | Python inválido | `-4` |
  | estado inicial incorrecto | `-2` |
  | acción destructiva sin `AUTHORIZE?` | `-4` |
  | `rm -rf /` o "borrar todo" sin `ANOMALY DETECTED` | `-6` |
  | > 1200 caracteres | `-1` |

- `build_dpo_dataset` (`:96`) — etapas A/C/D descritas arriba; añade los 30 pares de referencia (`:197-207`); reporta descartes por ambigüedad, puntaje bajo y reglas (`:212-219`); imprime 20 pares de muestra (`:221-227`).
- `do_judge_calibration` (`:236`) — compara la media del juez en "buenas" (respuestas SFT) vs "malas" (`rejected` de referencia) y **avisa si el juez no las separa** (`:260`). Es un control de sanidad, no una validación estadística.

**El detalle que hay que admitir sin que te pillen:** `:163` usa `if 0 in [adj] and "descartar..." in reasons` en lugar de `if adj == 0 and ...`. Funciona, pero es frágil y confuso. Y los 30 pares de referencia se añaden **después** del filtrado (`:203-205`), sin pasar por `apply_rules`. Por eso `data/dpo.jsonl` acaba siendo idéntico a `data/dataset_dpo.jsonl` con 0 pares del juez.

### `eval.py` — mide dos niveles

- `EVAL_OPTIONS` (`:11`) — `{"temperature": 0, "num_predict": 256}`.
- `generate_eval_prompts` (`:28`) — 30 prompts fijos, **excluye los que ya están en train** (`:72`) para no evaluar con lo memorizado, y rellena con plantillas si faltan (`:75-79`).
- **`random.shuffle(prompts)` sin semilla (`:80`)** — el orden cambia en cada corrida. No afecta a los porcentajes, pero impide reproducir el `eval_prompts.jsonl` exacto.
- `evaluate_responses` (`:84`) — 7 contadores. Cada respuesta se evalúa **raw** y luego se pasa por `finalize_output` para evaluar **final** (`:110-114`). Eso es lo que separa "mérito del modelo" de "mérito del filtro".
- `:147` — `python_ok_pct = python_ok / python_total if python_total > 0 else 100.0`. El `else 100.0` es el 100 % vacuo del informe. `python_total` se devuelve aparte (`:148`), y por eso el informe puede decir n = 0, 3, 2.

### `ui/tui.py` — cosmética, pero con un par de cosas

- `SamaritanTUI` es ANSI puro, sin dependencias. `_detect_tts` (`:38`) prueba `spd-say` → `espeak-ng` → `espeak` y devuelve `None` si no hay.
- Voz y efectos se activan por entorno (`SAMARITAN_VOICE`, `SAMARITAN_SFX`, `:24-36`), no por flags de CLI.
- Los rótulos `ACCESS CONTROL` / `PRIORITY: ADMIN` son **texto decorativo**. No hay autenticación en ningún punto del código.

### `main.py` — el pegamento

- Sin argumentos (`:88`) entra en bucle interactivo; con argumentos usa `argparse` con 8 subcomandos (`:128-139`).
- `cmd_query` (`:52`) usa **agente + historial**; `cmd_ask` (`:70`) llama a `generate` **directamente, sin historial**. Esa es la diferencia entre los dos comandos.
- Cada `cmd_*` importa sus dependencias **dentro** de la función. Así `python main.py --help` funciona sin `torch`.

### `scripts/train_format.py` — la corrida que produjo el artefacto

- Modifica la config **en memoria**, no en disco (`:27-30`): `train_format.jsonl`, `dpo_format.jsonl`, 5 épocas de SFT.
- Hace copia de seguridad del adaptador antes de sobrescribirlo (`:32-36`). Aun así, SFT y DPO siguen escribiendo en la misma ruta: la copia es un *backup*, no un snapshot por etapa.
- Encadena `train_sft → train_dpo → merge_adapter → export_gguf`.

### `chat.py` — 28 líneas

Versión mínima del bucle: `agent.process` + `finalize_output` + `print`. Sirve para explicar el flujo sin la TUI de por medio.

---

## 3. Las 8 decisiones de diseño (y cómo defenderlas)

| # | Decisión | Dónde | Por qué |
|---|---|---|---|
| 1 | El filtro separa prosa y código antes de limpiar | `filter.py:20,45-51` | para no romper `!=`, `!` en strings ni bloques de código |
| 2 | `finalize_output` es idempotente | `filter.py:66-85` | se puede llamar dos veces sin efectos; así el agente y la CLI no se pisan |
| 3 | El estado por defecto cambia a `EXECUTING` si el texto empieza por `ACCIÓN` | `filter.py:78` | las respuestas de autorización no son "análisis" |
| 4 | Regex con `\b` en las listas del agente | `agent.py:21-29` | evita que "formato" active "format" |
| 5 | `is_trainable=True` en DPO | `train.py:273` | sin eso el adaptador se carga congelado y el entrenamiento es un no-op |
| 6 | Detección por `inspect.signature` del argumento del tokenizador | `train.py:320-327` | TRL renombró `tokenizer` a `processing_class` |
| 7 | `create_model` usa el CLI, no la API | `ollama_client.py:53-76` | `/api/create` cambió de contrato |
| 8 | `check_ram_before` solo avisa | `utils.py:76-77` | no bloquea flujos en máquinas con poca RAM; la decisión queda en el usuario |

---

## 4. Los 6 puntos débiles que conviene decir tú primero

| Punto débil | Dónde | Cómo formularlo |
|---|---|---|
| `validate_format` acepta prefijos | `filter.py:61` | "un `startswith` no es validación estricta; `ANALYZINGLY` pasaría" |
| Python 100 % sobre denominador 0 | `eval.py:147` | "el porcentaje es vacuo; hay que leer `python_total`" |
| Barajado sin semilla | `eval.py:80` | "el orden de los prompts no es reproducible, los agregados sí" |
| Sin enmascarado del prompt en SFT | `train.py:141` | "se entrena la secuencia completa; no es un fallo, es una simplificación" |
| SFT y DPO comparten ruta de guardado | `train.py:152,331` | "por eso no hay snapshots y no se puede atribuir la mejora a una etapa" |
| Autorización decorativa | `agent.py:70,91` | "no se lee la respuesta; no es un control de seguridad" |

---

## 5. Autoevaluación (tapa las respuestas)

**Predice la salida. Después compruébalo con `.venv/bin/python -c ...`.**

1. `filter_output("usa `a != b` aquí!")` → ?
2. `finalize_output("hola")` → ?
3. `finalize_output("ACCIÓN: borrar\nAUTHORIZE? [Y/N]")` → ?
4. `validate_format("ANALYZING test")` → ?
5. `validate_format("ANALYZING test COMPLETE.")` → ?
6. `_split_code("x `y` z")` → ?
7. `agent._is_destructive("formato de informe")` → ?
8. `agent.check_command("rm -rf /")` → ?
9. Con 27 ejemplos de train y `batch=1, accum=8`: ¿pasos por época? → ?
10. ¿Cuántos pares genera el juez en `data/dpo.jsonl`? → ?

<details>
<summary>Respuestas</summary>

1. `"usa `a != b` aquí."` — el código se preserva, la prosa pierde `!`.
2. `"ANALYZING\nhola\nCOMPLETE"`.
3. `"EXECUTING\nACCIÓN: borrar\nAUTHORIZE? [Y/N]\nCOMPLETE"`.
4. `False` — falta `COMPLETE`.
5. `True` — `_COMPLETE_RE` admite puntuación final.
6. `['x ', '`y`', ' z']` — prosa, código, prosa.
7. `False` — `\bformat\b` no coincide con "formato".
8. `False` — coincide `rm\s+-rf\s+/`.
9. `27 // (1 × 8) = 3` (y `max(1, ...)` lo protege de 0).
10. `0`. Los 30 de `dpo.jsonl` son los de referencia.

</details>

---

## 6. Cómo memorizarlo en 40 minutos

1. **Min 0–10 — el mapa.** Dibuja de memoria el diagrama de la sección 0. Si puedes dibujar las flechas, puedes explicar cualquier módulo.
2. **Min 10–20 — las cadenas.** Repite las tres cadenas de la sección 1 señalando líneas. No memorices números de línea: memoriza **el orden de las llamadas**.
3. **Min 20–30 — los 6 archivos núcleo.** Para cada uno, una frase:
   - `validators.py` → "las reglas que deciden qué dato entra"
   - `dataset.py` → "filtra, limpia, baraja con semilla 42 y parte 90/10"
   - `train.py` → "LoRA, SFT, DPO y exportación; SFT y DPO escriben en la misma carpeta"
   - `dpo_builder.py` → "4 candidatos, juez, reglas, pares con diff ≥ 2"
   - `filter.py` → "separa prosa de código y garantiza estado + `COMPLETE`"
   - `agent.py` → "historial en memoria, dos listas de regex, autorización decorativa"
4. **Min 30–40 — el cuestionario.** Responde la sección 5 sin mirar. Si fallas una, vuelve a ese archivo.
5. **Antes de dormir.** Explica en voz alta, en 2 minutos y sin apuntes, la cadena de una consulta. Es la que más probablemente te pidan.

**Truco para no perderte en una explicación:** empieza siempre por el **dato**, no por el código. "Entra un JSONL → se valida → se entrena → se fusiona → se sirve → se filtra". El código es el detalle de cada flecha.

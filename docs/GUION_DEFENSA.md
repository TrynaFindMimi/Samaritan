# Guion de defensa — SAMARITAN

**Duración objetivo:** 9–10 min de exposición + preguntas.
**Base:** `docs/INFORME_SAMARITAN.md` (revisión del 2 de noviembre de 2026).
**Regla de oro:** el guion vende el *trabajo hecho* y adelanta los límites. Los límites no son debilidades: son la parte que demuestra criterio.

---

## 1. Mapa de memoria: 7 bloques, una idea cada uno

Memoriza **una frase ancla** por bloque. Si te pierdes, di el ancla y sigue.

| # | Bloque | Frase ancla (memorizar literal) | Tiempo |
|---|---|---|---|
| 1 | Gancho | "Un asistente que corre en tu máquina y respeta un contrato de salida." | 0:00–0:45 |
| 2 | Problema y objetivo | "No queremos competir con un asistente grande: queremos ver si uno de 0,5 B aprende un protocolo." | 0:45–1:45 |
| 3 | Cómo está hecho | "Cuatro piezas: datos filtrados, LoRA, SFT/DPO y un filtro determinista al final." | 1:45–3:45 |
| 4 | Recorrido de una consulta | "CLI, agente con memoria, Ollama local, filtro y TUI." | 3:45–4:45 |
| 5 | Resultados | "Cero por ciento, treinta y seis coma siete y cien por ciento en formato raw." | 4:45–6:45 |
| 6 | Límites | "Los pesos son trazables; el prompt no. Y el DPO es de formato, no de calidad." | 6:45–8:30 |
| 7 | Cierre | "Cumple el contrato de salida; no es un mecanismo de seguridad." | 8:30–9:30 |

---

## 2. Guion literal

> Léelo en voz alta dos veces y luego solo con las frases ancla. Las marcas `[PAUSA]` y `[FIGURA]` son para ti, no se dicen.

### Bloque 1 — Gancho (0:00–0:45)

Buenos días. Voy a presentar SAMARITAN: un agente conversacional que corre en local, sin APIs externas durante la inferencia, y que responde con un contrato de formato explícito.

La idea es simple de enunciar y difícil de cumplir: que un modelo pequeño aprenda a empezar con un estado, cerrar con `COMPLETE` y no usar emojis ni signos de exclamación.

`[PAUSA]` Hoy les voy a contar qué construimos, qué medimos y, sobre todo, qué **no** podemos afirmar con la evidencia que tenemos.

### Bloque 2 — Problema y objetivo (0:45–1:45)

El punto de partida es una dependencia: los asistentes basados en modelos de lenguaje suelen vivir en la nube. Eso trae cuatro problemas: privacidad, disponibilidad sin conexión, costo recurrente y poco control sobre el comportamiento.

Y hay un quinto problema, que es el que nos interesa: un modelo general no garantiza formato. Puede usar emojis, puede no cerrar, puede empezar como quiera.

Nuestro objetivo general fue diseñar e implementar un agente local que se ajuste a un protocolo de formato y seguridad definido, y evaluarlo con métricas de formato y pruebas unitarias.

`[PAUSA]` Quiero ser preciso: no intentamos competir con un asistente de gran escala. Intentamos ver si un modelo de 0,5 mil millones de parámetros puede adquirir un protocolo operativo reconocible, y si ese protocolo se puede reforzar en la salida.

### Bloque 3 — Cómo está hecho (1:45–3:45)

`[FIGURA 2]` El sistema tiene cuatro piezas.

**Primera: los datos.** Partimos de 30 ejemplos conversacionales. `data/dataset.py` los lee, descarta los que no cumplen el esquema y aplica validadores: emojis, exclamaciones y sintaxis de Python. De ahí salen 27 ejemplos de entrenamiento y 3 de evaluación.

**Segunda: la adaptación.** Usamos LoRA sobre `Qwen2.5-0.5B-Instruct`. Rango 16, alpha 32, dropout 0,05 y siete módulos. LoRA es clave aquí porque reduce muchísimo los parámetros que se actualizan: entrenamos en CPU, en FP32, con lote 1 y acumulación de gradientes de 8.

**Tercera: las dos etapas de ajuste.** Primero SFT, que enseña el protocolo con ejemplos: una época, tasa de dos por diez a la menos cuatro. Después DPO, que aprende de pares preferido/rechazado: beta 0,1, tasa de cinco por diez a la menos siete.

`[PAUSA]` Aquí hay un detalle que voy a retomar en los límites: SFT y DPO escriben en el **mismo** adaptador. No guardamos un snapshot "solo SFT" y otro "SFT más DPO".

**Cuarta: el filtro.** `output/filter.py` aplica `finalize_output()`. Limpia emojis y exclamaciones en la prosa, respeta los bloques de código y garantiza que la salida empiece con un estado válido y termine con `COMPLETE`.

Ese filtro es determinista. No depende del modelo. Y eso es intencional: el contrato se cumple aunque el modelo falle.

### Bloque 4 — Recorrido de una consulta (3:45–4:45)

`[FIGURA 1]` Cuando el usuario escribe, pasa esto.

La CLI de `main.py` recibe la consulta. `SamaritanAgent` la añade al historial en memoria, revisa palabras clave asociadas a acciones destructivas y, si no hay coincidencia, llama al modelo.

La llamada va a `serving/ollama_client.py`, que habla con la API local de Ollama en `/api/chat`. La respuesta vuelve al agente, pasa por el filtro y se muestra en la TUI.

Todo el ciclo de vida está centralizado: `config.yaml` y los comandos `build-data`, `train-sft`, `create-model`, `build-dpo`, `train-dpo`, `eval` y `query`.

`[PAUSA]` La TUI muestra rótulos como `ACCESS CONTROL` y `PRIORITY: ADMIN`. Son decorativos. No hay autenticación real detrás, y lo digo explícitamente porque es fácil confundirlo.

### Bloque 5 — Resultados (4:45–6:45)

`[FIGURA 3 / TABLA 5]` Lo primero: la suite. **29 pruebas aprobadas, 0 fallidas, en 0,51 segundos.** Cubren validadores, reglas del DPO y el filtro de salida.

Lo segundo, y es el centro del informe: la evaluación de formato. 30 prompts fijos, temperatura 0, 256 tokens de salida, tres variantes.

Los números que hay que retener son tres filas.

Sin emojis ni exclamaciones: base por defecto 86,7 por ciento; base con el prompt desplegado, 100; Samaritan, 100.

Raw Inicio, es decir, que la respuesta cruda empiece con un estado válido: **0, 90 y 100 por ciento.**

Raw Formato, que es inicio **y** cierre con `COMPLETE`: **0, 36,7 y 100 por ciento.**

`[PAUSA]` Esos son los tres números del proyecto. Cero, treinta y seis coma siete, cien.

Y un cuarto dato que hay que decir siempre: la salida final llega a 100 por ciento en las tres variantes. Pero eso **no** es mérito del modelo: es el filtro cumpliendo su contrato.

La interpretación honesta es esta. El prompt por sí solo ya sube el inicio de 0 a 90 por ciento. O sea, parte de la mejora viene del prompt, no del adaptador. Lo que el prompt no logra es el cierre: ahí se queda en 36,7. El modelo ajustado sí cierra: 100 por ciento.

En tiempo: 225 segundos el base por defecto, 108 el base con prompt, 152 Samaritan. Son tiempos descriptivos, de una sola corrida en CPU. No son un benchmark.

### Bloque 6 — Límites (6:45–8:30)

`[PAUSA]` Ahora la parte que más me interesa defender.

**Uno: no hay snapshots separados.** SFT y DPO escriben en `model/lora_adapter/`. Los checkpoints 4 a 40 son de una corrida anterior. Entonces no puedo afirmar que la mejora se deba a SFT o a DPO. La comparación válida es base, base con prompt y modelo final. No es SFT contra SFT más DPO.

**Dos: el DPO es de formato.** `data/dpo.jsonl` es idéntico a `data/dataset_dpo.jsonl`: 30 pares de referencia y **cero** pares generados por el juez. El juez generó 40 candidatos, pero no llegaron al artefacto. Entonces el adaptador aprendió a envolver respuestas con el contrato; no aprendió necesariamente a preferir respuestas mejores.

**Tres: el prompt no está versionado.** El prompt desplegado tiene 4217 caracteres y 155 líneas. Usa temperatura 0,1. El `Modelfile` del repositorio usa temperatura 0,3 y un prompt distinto. Los pesos sí son trazables: el GGUF tiene hash SHA-256 y coincide con el blob de Ollama. El prompt no. La frase es: **pesos trazables, prompt no trazable.**

**Cuatro: el filtro garantiza formato, no calidad.** Una respuesta puede ser formalmente válida y factualmente falsa. `finalize_output()` no valida semántica.

**Cinco: no es un mecanismo de seguridad.** La detección de acciones destructivas es textual, no cubre variantes como "formatea" o "reinicia", y la solicitud `AUTHORIZE?` no verifica nada ni ejecuta comandos.

Y una sexta, más fina: el 100 por ciento de Python válido es vacuo. El denominador es 0, 3 y 2 bloques según la variante. Un 100 sobre 0 no demuestra nada.

### Bloque 7 — Cierre (8:30–9:30)

Sintetizo.

SAMARITAN integra un ciclo completo y verificable en sus componentes: datos, LoRA, SFT, DPO, fusión, GGUF, serving local, agente, filtro y TUI. Las 29 pruebas pasan. Y el modelo ajustado cumple el formato raw en 30 de 30 respuestas, mientras el base por defecto cumple 0 de 30.

Lo que no puedo decir es que SFT o DPO mejoraron el modelo por separado, ni que el DPO aprendió preferencias de calidad, ni que el sistema sea seguro para ejecutar acciones reales.

`[PAUSA]` Por eso el proyecto vale como base experimental, no como producto. Y el trabajo futuro está claro: versionar el prompt, guardar snapshots por etapa, repetir la evaluación con más prompts y añadir validación semántica y humana.

Gracias. Quedo atento a sus preguntas.

---

## 3. Versión de 3 minutos (si te recortan el tiempo)

1. **Qué es:** agente local con Ollama sobre Qwen2.5-0.5B, LoRA, SFT y DPO, con un contrato de salida `ESTADO … COMPLETE` forzado por un filtro determinista.
2. **Cómo:** 30 ejemplos filtrados → 27 de train y 3 de eval; LoRA r=16 y alpha=32 en CPU FP32; SFT una época; DPO beta 0,1; juez `qwen2.5:3b`; serving en `/api/chat`; CLI y TUI.
3. **Resultado:** 29 pruebas en 0,51 s. Formato raw válido: 0 por ciento base, 36,7 base con prompt, 100 Samaritan. Final 100 en las tres variantes, pero por el filtro.
4. **Límite:** no hay snapshots por etapa, el DPO es de formato con 0 pares del juez, el prompt desplegado no está versionado y el sistema no es un mecanismo de seguridad.
5. **Cierre:** cumple el contrato de salida; no demuestra calidad semántica ni mejora causal de SFT/DPO.

---

## 4. Si te preguntan

Respuestas cortas, con el número a mano. No improvises cifras: si no la tienes, di "ese dato no lo medimos".

| Pregunta | Respuesta |
|---|---|
| ¿Por qué 0,5 B y no un modelo mayor? | Objetivo de diseño: hardware modesto y ciclo completo. El informe no mide memoria máxima ni duración total, así que no lo presentamos como resultado medido. |
| ¿Por qué LoRA y no fine-tuning completo? | Reduce los parámetros actualizados. Eso no prueba por sí solo que quepa en un límite de memoria concreto. |
| ¿Qué aporta DPO si el resultado es el mismo filtro? | El DPO desplegado enseña el contrato de formato: `chosen` es la referencia envuelta con `ANALYZING` y `COMPLETE`, `rejected` es la misma sin formato. No aporta preferencias del juez. |
| ¿El juez funcionó? | Generó 40 candidatos y los puntuó, pero 0 pares llegaron al artefacto final. El juez no está validado contra anotaciones humanas. |
| ¿Entonces el juez es inútil? | No: está implementado y documentado. Lo que falta es usarlo como señal y medir su acuerdo con humanos. |
| ¿Por qué el 100 por ciento de Python no vale? | Porque el denominador es 0, 3 y 2. Hay que informar cuántos bloques se detectaron. |
| ¿El modelo es seguro? | No como mecanismo de seguridad. Hay tres capas parciales: prompt, reglas textuales y filtro. Ninguna autoriza ni ejecuta. |
| ¿Puedo reproducir la evaluación? | Parcialmente. Faltan el prompt desplegado exacto y sus parámetros. Los pesos sí: el GGUF tiene hash y coincide con el blob de Ollama. |
| ¿Cuál es la mejora más sólida? | Raw Formato de 0 a 100 por ciento con 30 prompts. Es la evidencia más fuerte a favor del entrenamiento de formato, aunque no separa SFT de DPO. |
| ¿Qué cambiarías primero? | Versionar el prompt y guardar snapshots por etapa. Sin eso, ninguna comparación causal es posible. |
| ¿Por qué el filtro no es trampa? | Porque está declarado como parte del sistema y se reporta aparte: raw mide el modelo y final mide el sistema. |
| ¿Qué pasa con `validate_format()`? | Tiene un caso límite: el prefijo puede coincidir dentro de otra palabra. Está en trabajo futuro. |

**Frases que NO debes decir** (y su reemplazo):

| No digas | Di |
|---|---|
| "SFT y DPO mejoraron el modelo" | "El modelo final mejora el formato; no se puede aislar la etapa" |
| "El juez entrenó el DPO" | "El DPO desplegado es de formato; 0 pares del juez" |
| "El sistema es seguro" | "El sistema tiene controles parciales de formato, no de seguridad" |
| "El 100 por ciento de Python está validado" | "100 por ciento sobre 0, 3 y 2 bloques" |
| "El modelo está completamente documentado" | "Los pesos son trazables; el prompt no" |

---

## 5. Chuleta de cifras (memorizar como una sola lista)

**29 / 0 / 0,51** — pruebas aprobadas, fallidas, segundos. 6 archivos de prueba.

**0 / 36,7 / 100** — Raw Formato: base, base+prompt, Samaritan.

**0 / 90 / 100** — Raw Inicio, misma secuencia.

**100 / 100 / 100** — Final OK, por `finalize_output()`.

**30 prompts · temperatura 0 · 256 tokens** — configuración de la evaluación.

**16 / 32 / 0,05 / 7** — LoRA: rango, alpha, dropout, módulos.

**2e-4 / 5e-7 / 0,1** — LR de SFT, LR de DPO, beta de DPO.

**30 / 27 / 3 / 30 / 40 / 30 / 30** — dataset_sft, train, eval, dataset_dpo, candidatos, dpo, dpo_format.

**494,03 M · 949 MB · 994 MB · 397 MB** — GGUF F16 (parámetros, tamaño), Samaritan en Ollama, base en Ollama.

**4217 / 155 / 0,1 / 0,3** — prompt desplegado (caracteres, líneas), temperatura desplegada, temperatura del `Modelfile`.

**225 / 108 / 152 s** — tiempos por 30 prompts.

**Hash:** `4495616c…c044fd0` — no lo recites completo; di "SHA-256 verificado y coincidente con el blob de Ollama".

---

## 6. Cómo memorizarlo en poco tiempo

1. **Pasada 1 (15 min):** lee el guion completo en voz alta una vez. No memorices, solo entiende el orden.
2. **Pasada 2 (15 min):** memoriza solo las 7 frases ancla de la tabla del inicio. Di la presentación entera usando únicamente esas frases, improvisando el resto.
3. **Pasada 3 (10 min):** memoriza la chuleta de cifras como bloques de tres. Repítela en voz alta: "cero, treinta y seis coma siete, cien".
4. **Pasada 4 (10 min):** ensaya las respuestas de "Si te preguntan" en voz alta, en 20 segundos cada una.
5. **Antes de entrar:** relee solo la tabla de frases ancla y la lista de "No digas".

**Truco de transición:** cada bloque termina con una frase puente. Si olvidas el siguiente, usa el puente:
*"Y eso nos lleva a…"* → método. *"Pero hay un detalle"* → límites. *"Sintetizo"* → cierre.

**Si te quedas en blanco:** di el dato más fuerte que recuerdes —*"cero, treinta y seis coma siete, cien"*— y desde ahí reconstruye el bloque de resultados.

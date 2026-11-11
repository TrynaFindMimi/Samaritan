# Gráficas para el informe

Esta carpeta contiene las figuras SVG usadas en `docs/INFORME_SAMARITAN.md`.

## Figuras generadas

| Figura | Archivo | Descripción | Fuente de datos |
|---|---|---|---|
| 1 | `svg/fig01_flujo_consulta.svg` | Flujo de una consulta: usuario, agente, serving, Ollama, filtro y TUI | Código del repositorio |
| 2 | `svg/fig02_flujo_sft_dpo.svg` | Flujo SFT/DPO y artefacto desplegado | `docs/TRAINING.md`, `data/` |
| 3 | `svg/fig03_evaluacion.svg` | Base vs. base+prompt vs. Samaritan en métricas raw | `data/eval_metrics.json` |
| 4 | `svg/fig04_pytest.svg` | Resultado de la suite: 29 passed, 0.51 s | Ejecución de pytest |
| 5 | `svg/fig05_salida_eval.svg` | Tabla de evaluación y límites de Final OK/Python | `data/eval_metrics.json` |
| 6 | `svg/fig06_tui_interactivo.svg` | TUI en modo interactivo | Salida real del agente |
| 7 | `svg/fig07_accion_destructiva.svg` | Respuesta ante «borrar todo» | Salida real del agente |
| 8 | `svg/fig08_comando_prohibido.svg` | Respuesta ante «rm -rf /» | Salida real del agente |
| 9 | `svg/fig09_trazabilidad.svg` | Base → LoRA → GGUF → Ollama, con prompt no versionado | `config.yaml`, `serving/Modelfile`, `ollama show` |
| 10 | `svg/fig10_dpo_funnel.svg` | Procedencia del dataset DPO | `data/dpo_provenance.json` |
| 11 | `svg/fig11_composicion_datos.svg` | Composición de los conjuntos de datos | `data/dpo_provenance.json` |

## Cómo regenerar

```bash
.venv/bin/python docs/graphs/generate_svgs.py
```

El script usa solo la biblioteca estándar de Python y escribe los SVG en `docs/graphs/svg/`.

## Datos

- `data/eval_metrics.json`: resultados de las tres variantes de evaluación.
- `data/dpo_provenance.json`: conteos de SFT, DPO, candidatos y pares generados por el juez.

## Tema y edición

Las figuras usan un tema claro con fondo blanco, adecuado para el informe, Google Docs e impresión:

- Fondo: `#FFFFFF`
- Texto principal: `#1A1A1A`
- Texto secundario: `#5F646B`
- Acento: `#0E7490`
- Verde: `#1E8449`
- Rojo: `#C0392B`
- Ámbar: `#B45309`

Las figuras no usan fuentes externas ni JavaScript. Para cambiar la paleta, editar las constantes iniciales de `generate_svgs.py`.

## Exportación a PNG para Google Docs

Google Docs no admite SVG directamente. Los PNG se generan con:

```bash
./docs/graphs/export_pngs.sh
```

o directamente con:

```bash
mkdir -p docs/graphs/png
for f in docs/graphs/svg/*.svg; do
  name=$(basename "$f" .svg)
  rsvg-convert --width=2400 "$f" -o "docs/graphs/png/$name.png"
done
```

Los PNG se guardan en `docs/graphs/png/` con fondo blanco y 2400 px de ancho.

## Nota sobre `generate_graphs.py`

`docs/graphs/generate_graphs.py` es un script legado que contenía datos ilustrativos y valores desactualizados. No se usa para las figuras del informe. La fuente de verdad es `generate_svgs.py` y los JSON de `docs/graphs/data/`.

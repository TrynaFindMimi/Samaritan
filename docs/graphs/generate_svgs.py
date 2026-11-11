#!/usr/bin/env python3
"""Genera las figuras SVG del informe SAMARITAN.

Uso:
    .venv/bin/python docs/graphs/generate_svgs.py

Salida:
    docs/graphs/svg/fig01_flujo_consulta.svg
    docs/graphs/svg/fig02_flujo_sft_dpo.svg
    ...
    docs/graphs/svg/fig11_composicion_datos.svg

Sin dependencias externas: solo la biblioteca estándar. Los datos de
evaluación y de procedencia DPO se leen de docs/graphs/data/*.json.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "svg"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Paleta y tipografías
# ---------------------------------------------------------------------------

BG = "#FFFFFF"
BG_TOP = "#F7F7F5"
PANEL = "#F3F3EE"
PANEL_2 = "#EDEDE8"
BORDER = "#C9C9C2"
GRID = "#E3E3DE"
BONE = "#1A1A1A"
MUTED = "#5F646B"
CYAN = "#0E7490"
GREEN = "#1E8449"
RED = "#C0392B"
AMBER = "#B45309"
BLUE = "#1D4ED8"
PURPLE = "#6D28D9"
GRAY = "#4B5563"

SANS = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

MARKER_COLORS = {
    "cyan": CYAN,
    "green": GREEN,
    "red": RED,
    "amber": AMBER,
    "bone": BONE,
    "muted": MUTED,
    "purple": PURPLE,
    "blue": BLUE,
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=False)


def _attrs(**kwargs: object) -> str:
    parts = []
    for key, value in kwargs.items():
        if value is None:
            continue
        key = key.replace("_", "-")
        parts.append(f'{key}="{esc(value)}"')
    return " ".join(parts)


def text(
    x: float,
    y: float,
    value: object,
    *,
    fill: str = BONE,
    size: int = 18,
    family: str = SANS,
    weight: str = "normal",
    anchor: str = "start",
    opacity: float | None = None,
    letter_spacing: float | None = None,
    style: str | None = None,
    transform: str | None = None,
) -> str:
    attributes = _attrs(
        x=x,
        y=y,
        fill=fill,
        font_size=size,
        font_family=family,
        font_weight=weight,
        text_anchor=anchor,
        opacity=opacity,
        letter_spacing=letter_spacing,
        font_style=style,
        transform=transform,
    )
    return f"<text {attributes}>{esc(value)}</text>"


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = PANEL,
    stroke: str | None = None,
    stroke_width: float = 1,
    rx: float = 0,
    opacity: float | None = None,
    dash: str | None = None,
) -> str:
    attributes = _attrs(
        x=x,
        y=y,
        width=w,
        height=h,
        fill=fill,
        stroke=stroke,
        stroke_width=stroke_width,
        rx=rx,
        opacity=opacity,
        stroke_dasharray=dash,
    )
    return f"<rect {attributes}/>"


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = BORDER,
    width: float = 2,
    dash: str | None = None,
    opacity: float | None = None,
    marker_end: str | None = None,
    marker_start: str | None = None,
) -> str:
    attributes = _attrs(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        stroke=stroke,
        stroke_width=width,
        stroke_dasharray=dash,
        opacity=opacity,
        marker_end=marker_end,
        marker_start=marker_start,
    )
    return f"<line {attributes}/>"


def path(
    d: str,
    *,
    fill: str = "none",
    stroke: str | None = None,
    width: float = 2,
    dash: str | None = None,
    opacity: float | None = None,
    marker_end: str | None = None,
    marker_start: str | None = None,
) -> str:
    attributes = _attrs(
        d=d,
        fill=fill,
        stroke=stroke,
        stroke_width=width,
        stroke_dasharray=dash,
        opacity=opacity,
        marker_end=marker_end,
        marker_start=marker_start,
    )
    return f"<path {attributes}/>"


def circle(
    cx: float,
    cy: float,
    r: float,
    *,
    fill: str = CYAN,
    stroke: str | None = None,
    width: float = 1,
    opacity: float | None = None,
) -> str:
    attributes = _attrs(
        cx=cx,
        cy=cy,
        r=r,
        fill=fill,
        stroke=stroke,
        stroke_width=width,
        opacity=opacity,
    )
    return f"<circle {attributes}/>"


def arrow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    color: str = CYAN,
    width: float = 2,
    dash: str | None = None,
    opacity: float | None = None,
) -> str:
    return line(
        x1,
        y1,
        x2,
        y2,
        stroke=color,
        width=width,
        dash=dash,
        opacity=opacity,
        marker_end=f"url(#arrow-{color_key(color)})",
    )


def elbow_arrow(
    points: list[tuple[float, float]],
    *,
    color: str = CYAN,
    width: float = 2,
    dash: str | None = None,
) -> str:
    """Dibuja una polilínea ortogonal con punta de flecha."""
    if len(points) < 2:
        return ""
    d = f"M {points[0][0]} {points[0][1]}"
    for x, y in points[1:]:
        d += f" L {x} {y}"
    return path(
        d,
        stroke=color,
        width=width,
        dash=dash,
        marker_end=f"url(#arrow-{color_key(color)})",
    )


def color_key(color: str) -> str:
    for key, value in MARKER_COLORS.items():
        if value == color:
            return key
    return "cyan"


def marker_defs() -> str:
    items = []
    for key, color in MARKER_COLORS.items():
        items.append(
            f'<marker id="arrow-{key}" viewBox="0 0 10 10" refX="9" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
        )
    return "\n    ".join(items)


def svg_document(
    width: int,
    height: int,
    title: str,
    desc: str,
    body: list[str],
) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{esc(title)}</title>
  <desc id="desc">{esc(desc)}</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{BG_TOP}"/>
      <stop offset="1" stop-color="{BG}"/>
    </linearGradient>
    {marker_defs()}
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <rect x="0" y="0" width="{width}" height="3" fill="{CYAN}" opacity="0.75"/>
  {''.join(body)}
</svg>
"""


def header(fig: str, title: str, subtitle: str) -> list[str]:
    return [
        text(60, 44, fig, fill=CYAN, size=13, weight="600", letter_spacing=2.4),
        text(60, 82, title, fill=BONE, size=31, weight="600"),
        text(60, 110, subtitle, fill=MUTED, size=16),
        line(60, 128, 1140, 128, stroke=BORDER, width=1),
    ]


def footer(lines: list[str], *, y: int = 665) -> list[str]:
    out = []
    for index, value in enumerate(lines):
        out.append(text(60, y + index * 22, value, fill=MUTED, size=13.5))
    return out


def panel(x: float, y: float, w: float, h: float, *, fill: str = PANEL) -> str:
    return rect(x, y, w, h, fill=fill, stroke=BORDER, stroke_width=1, rx=16)


def flow_box(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    sub_lines: list[str],
    *,
    color: str = CYAN,
    fill: str = PANEL,
    dash: str | None = None,
    title_size: int = 17,
) -> list[str]:
    out = [
        rect(x, y, w, h, fill=fill, stroke=color, stroke_width=1.4, rx=12, dash=dash),
        rect(x, y + 12, 4, h - 24, fill=color, rx=2),
        text(x + 20, y + 32, title, fill=BONE, size=title_size, weight="600"),
    ]
    for index, line_value in enumerate(sub_lines):
        out.append(text(x + 20, y + 57 + index * 19, line_value, fill=MUTED, size=13))
    return out


def centered_box(
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    sub_lines: list[str],
    *,
    color: str = CYAN,
    fill: str = PANEL,
    dash: str | None = None,
) -> list[str]:
    out = [
        rect(x, y, w, h, fill=fill, stroke=color, stroke_width=1.4, rx=12, dash=dash),
        text(x + w / 2, y + 34, title, fill=color, size=16, weight="600", anchor="middle"),
    ]
    for index, line_value in enumerate(sub_lines):
        out.append(
            text(
                x + w / 2,
                y + 58 + index * 19,
                line_value,
                fill=BONE if index == 0 else MUTED,
                size=13.5 if index == 0 else 12.5,
                anchor="middle",
            )
        )
    return out


def legend_item(x: float, y: float, color: str, label: str, *, size: int = 14) -> list[str]:
    return [
        rect(x, y - 11, 14, 14, fill=color, rx=3),
        text(x + 24, y + 1, label, fill=BONE, size=size),
    ]


# ---------------------------------------------------------------------------
# FIGURA 1 - Flujo de consulta
# ---------------------------------------------------------------------------


def fig01() -> str:
    body = header(
        "FIGURA 1",
        "Flujo de una consulta",
        "Del mensaje del usuario a la respuesta filtrada que ve la TUI",
    )

    y = 235
    w = 165
    h = 112
    boxes = [
        (45, "USUARIO / CLI", ["main.py", "query · ask · REPL"]),
        (235, "AGENTE", ["SamaritanAgent", "historial + políticas"]),
        (425, "SERVING", ["ollama_client.py", "generate()"]),
        (615, "OLLAMA LOCAL", ["samaritan", "localhost:11434"]),
        (805, "FILTRO", ["output/filter.py", "finalize_output()"]),
        (995, "TUI", ["ui/tui.py", "respuesta final"]),
    ]
    for x, title, sub in boxes:
        body.extend(flow_box(x, y, w, h, title, sub))

    for x in (210, 400, 590, 780, 970):
        body.append(arrow(x + 2, y + h / 2, x + 27, y + h / 2, color=CYAN, width=2))

    body.extend(
        [
            panel(45, 420, 1115, 140, fill=PANEL_2),
            text(70, 455, "RAMAS DE POLÍTICA", fill=AMBER, size=14, weight="600", letter_spacing=1.6),
            text(
                70,
                488,
                "El agente intercepta comandos prohibidos y solicitudes destructivas antes de llamar al modelo.",
                fill=BONE,
                size=15,
            ),
            text(
                70,
                516,
                "Esas ramas se detallan en las Figuras 7 y 8. La TUI solo recibe la salida ya filtrada.",
                fill=MUTED,
                size=14,
            ),
            text(
                70,
                544,
                "Única frontera con el modelo: serving/ollama_client.py. Única frontera de contrato: output/filter.py.",
                fill=MUTED,
                size=13,
            ),
        ]
    )

    body.extend(
        footer(
            [
                "Figura 1. El filtro se aplica en todos los caminos, incluidos los errores y las ramas de política.",
                "La TUI no habla con Ollama: solo muestra texto que ya pasó por finalize_output().",
            ],
            y=640,
        )
    )
    return svg_document(
        1200,
        700,
        "Flujo de consulta de SAMARITAN",
        "Diagrama de flujo: usuario, agente, serving, Ollama, filtro y TUI, con las ramas de política.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 2 - Flujo SFT / DPO
# ---------------------------------------------------------------------------


def fig02() -> str:
    body = header(
        "FIGURA 2",
        "Flujo de datos y entrenamiento",
        "SFT y DPO comparten el mismo adaptador; el DPO desplegado es de formato",
    )

    body.append(text(50, 175, "SFT", fill=CYAN, size=14, weight="700", letter_spacing=2))
    sft = [
        (50, "dataset_sft.jsonl", ["30 ejemplos"]),
        (275, "build_datasets()", ["27 train / 3 eval"]),
        (500, "train_format.jsonl", ["27 con formato"]),
        (725, "train_sft()", ["20 pasos", "loss 1,967"]),
        (950, "lora_adapter", ["r=16 · α=32", "7 módulos"]),
    ]
    y1 = 195
    w1 = 200
    h1 = 105
    for x, title, sub in sft:
        body.extend(flow_box(x, y1, w1, h1, title, sub, color=CYAN, title_size=15))
    for x in (250, 475, 700, 925):
        body.append(arrow(x + 2, y1 + h1 / 2, x + 23, y1 + h1 / 2, color=CYAN))

    body.append(text(50, 355, "DPO", fill=AMBER, size=14, weight="700", letter_spacing=2))
    dpo = [
        (20, "train.jsonl", ["27 prompts"]),
        (218, "candidates.jsonl", ["10 prompts × 4", "= 40 candidatos"]),
        (416, "juez + reglas", ["0 pares usados"], RED),
        (614, "dataset_dpo.jsonl", ["30 de referencia"], AMBER),
        (812, "dpo_format.jsonl", ["30 sintéticos"], CYAN),
        (1010, "train_dpo()", ["4 pasos", "loss 0,6873"], GREEN),
    ]
    y2 = 375
    w2 = 178
    h2 = 112
    for item in dpo:
        x, title, sub = item[:3]
        color = item[3] if len(item) == 4 else AMBER
        body.extend(flow_box(x, y2, w2, h2, title, sub, color=color, title_size=13.0))
    for x in (198, 396, 594, 792, 990):
        body.append(arrow(x + 2, y2 + h2 / 2, x + 18, y2 + h2 / 2, color=AMBER))

    # El juez no alimenta el artefacto final.
    body.extend(
        [
            elbow_arrow(
                [(505, y2 + h2 + 4), (505, 565), (901, 565)],
                color=RED,
                width=1.8,
                dash="6 6",
            ),
            line(891, 555, 911, 575, stroke=RED, width=2.2),
            line(911, 555, 891, 575, stroke=RED, width=2.2),
            text(520, 555, "0 pares: no llegan al artefacto", fill=RED, size=13, weight="600"),
            text(520, 580, "data/dpo.jsonl == data/dataset_dpo.jsonl", fill=RED, size=12.5),
        ]
    )

    body.extend(
        [
            panel(50, 590, 1100, 100, fill=PANEL_2),
            text(72, 622, "QUÉ SE DESPLEGÓ", fill=GREEN, size=13, weight="700", letter_spacing=1.6),
            text(
                72,
                650,
                "El adaptador final se fusionó con Qwen2.5-0.5B-Instruct y se exportó como GGUF F16.",
                fill=BONE,
                size=14.5,
            ),
            text(
                72,
                674,
                "El DPO es de formato: chosen = ANALYZING + referencia + COMPLETE; rejected = referencia sin formato.",
                fill=MUTED,
                size=13.5,
            ),
        ]
    )

    body.extend(
        footer(
            [
                "Figura 2. No existen snapshots separados de SFT y DPO: ambos escriben en model/lora_adapter/.",
            ],
            y=730,
        )
    )
    return svg_document(
        1200,
        790,
        "Flujo de datos y entrenamiento SFT/DPO",
        "Diagrama de las dos etapas: SFT con 27 ejemplos y DPO de formato con 30 pares; el juez generó 0 pares usados.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 3 - Evaluación comparativa
# ---------------------------------------------------------------------------


def load_json(name: str) -> dict:
    with (DATA / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def fig03() -> str:
    data = load_json("eval_metrics.json")
    variants = data["variants"]

    body = header(
        "FIGURA 3",
        "Evaluación de formato: base vs. prompt vs. modelo ajustado",
        "30 prompts fijos · salida cruda (raw) · temperature=0 · num_predict=256",
    )

    # Leyenda
    legend_y = 165
    for index, variant in enumerate(variants):
        color = [GRAY, AMBER, GREEN][index]
        body.extend(legend_item(700 + index * 150, legend_y, color, variant["label"], size=13))

    # Área de trazo
    x0, x1 = 105, 1130
    y0, y1 = 205, 560  # y0 = 100 %, y1 = 0 %
    body.append(line(x0, y1, x1, y1, stroke=BORDER, width=1.2))
    for value in (0, 25, 50, 75, 100):
        y = y1 - (value / 100) * (y1 - y0)
        body.append(line(x0, y, x1, y, stroke=GRID, width=1))
        body.append(text(x0 - 15, y + 5, f"{value}%", fill=MUTED, size=13, anchor="end"))
    axis_label_y = (y0 + y1) / 2
    body.append(
        text(
            38,
            axis_label_y,
            "Respuestas (%)",
            fill=MUTED,
            size=13,
            anchor="middle",
            style="normal",
            transform=f"rotate(-90 38 {axis_label_y})",
        )
    )

    metrics = [
        ("no_emoji", "Sin emojis / !"),
        ("raw_start", "Raw inicio"),
        ("raw_format", "Raw formato"),
    ]
    group_centers = [280, 640, 1000]
    group_width = 300
    bar_w = 58
    gap = 12
    colors = [GRAY, AMBER, GREEN]

    for group_index, (metric_key, label) in enumerate(metrics):
        center = group_centers[group_index]
        total = len(variants) * bar_w + (len(variants) - 1) * gap
        start = center - total / 2
        for series_index, variant in enumerate(variants):
            value = variant["metrics"][metric_key]
            x = start + series_index * (bar_w + gap)
            height = (value / 100) * (y1 - y0)
            y = y1 - height
            body.append(
                rect(
                    x,
                    y,
                    bar_w,
                    max(height, 1.5),
                    fill=colors[series_index],
                    rx=4,
                    opacity=0.95,
                )
            )
            label_color = BONE if value > 0 else MUTED
            body.append(
                text(
                    x + bar_w / 2,
                    y - 10 if value > 0 else y1 - 10,
                    f"{value:.1f}%",
                    fill=label_color,
                    size=12.5,
                    weight="600",
                    anchor="middle",
                )
            )
        body.append(text(center, y1 + 30, label, fill=BONE, size=15, weight="600", anchor="middle"))
        body.append(text(center, y1 + 50, f"n={data['prompts']}", fill=MUTED, size=12, anchor="middle"))

    body.extend(
        [
            rect(105, 630, 1025, 58, fill=PANEL_2, stroke=BORDER, rx=10),
            text(
                125,
                654,
                "Final OK = 100% en las tres variantes por construcción de finalize_output().",
                fill=BONE,
                size=13.5,
            ),
            text(
                125,
                675,
                "No se grafica como mérito del modelo: es una garantía del contrato de salida, no una medida de calidad.",
                fill=MUTED,
                size=12.5,
            ),
        ]
    )
    return svg_document(
        1200,
        700,
        "Evaluación comparativa de formato",
        "Barras agrupadas: base por defecto, base con el prompt desplegado y Samaritan; métricas sin emojis, inicio raw y formato raw.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 4 - Pruebas unitarias
# ---------------------------------------------------------------------------


def fig04() -> str:
    body = header(
        "FIGURA 4",
        "Pruebas unitarias",
        "Suite ejecutada en el entorno del proyecto el 2 de noviembre de 2026",
    )

    body.append(panel(80, 165, 1040, 330, fill=PANEL_2))
    # Barra de ventana
    body.extend(
        [
            circle(110, 190, 6, fill=RED),
            circle(132, 190, 6, fill=AMBER),
            circle(154, 190, 6, fill=GREEN),
            text(1050, 195, "pytest -q", fill=MUTED, size=12.5, anchor="end"),
        ]
    )
    body.append(line(80, 210, 1120, 210, stroke=BORDER, width=1))

    terminal = [
        ("$ source .venv/bin/activate", MUTED),
        ("$ python -m pytest -q", BONE),
        ("", BONE),
        (".............................                                      [100%]", MUTED),
        ("29 passed in 0.51s", GREEN),
    ]
    for index, (value, color) in enumerate(terminal):
        body.append(
            text(
                115,
                252 + index * 34,
                value,
                fill=color,
                size=18 if index < 3 else 17,
                family=MONO,
                weight="600" if index == 4 else "normal",
            )
        )

    cards = [
        ("29", "PASSED", GREEN),
        ("0", "FAILED", RED),
        ("0.51 s", "TIEMPO", CYAN),
    ]
    for index, (value, label, color) in enumerate(cards):
        x = 80 + index * 350
        body.append(rect(x, 525, 320, 105, fill=PANEL, stroke=BORDER, rx=12))
        body.append(text(x + 24, 570, value, fill=color, size=32, weight="700"))
        body.append(text(x + 24, 600, label, fill=MUTED, size=12.5, weight="600", letter_spacing=1.5))

    body.extend(
        footer(
            [
                "Figura 4. Python 3.14.8 · 6 archivos de prueba · 29 tests, 0 fallos.",
                "La suite cubre agente, filtro de salida, cliente Ollama, datos y evaluación; no cubre calidad semántica.",
            ],
            y=665,
        )
    )
    return svg_document(
        1200,
        700,
        "Resultado de las pruebas unitarias",
        "Tarjeta de terminal con 29 pruebas aprobadas en 0.51 segundos y cero fallos.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 5 - Tabla de evaluación
# ---------------------------------------------------------------------------


def fig05() -> str:
    data = load_json("eval_metrics.json")
    variants = data["variants"]

    body = header(
        "FIGURA 5",
        "Salida de evaluación",
        "Comparación de las tres variantes medidas con los 30 prompts fijos",
    )

    x = 60
    y = 170
    widths = [205, 125, 115, 115, 125, 125, 110, 110]
    headers = ["Versión", "Sin emojis/!", "Raw inicio", "Raw estado", "Raw formato", "Final inicio", "Final OK", "Python"]
    row_h = 72
    table_w = sum(widths)

    body.append(rect(x, y, table_w, row_h + 3 * row_h + 8, fill=PANEL, stroke=BORDER, rx=12))
    body.append(rect(x, y, table_w, row_h, fill="#E8E8E3", rx=12))
    body.append(rect(x, y + row_h - 12, table_w, 12, fill="#E8E8E3"))

    cursor = x
    for width, label in zip(widths, headers):
        body.append(text(cursor + 14, y + 43, label, fill=CYAN, size=12.5, weight="600"))
        cursor += width

    row_colors = [PANEL, "#E8E8E3", "#DCEFF2"]
    metric_keys = ["no_emoji", "raw_start", "raw_state", "raw_format", "final_start", "final_format", "python_ok"]

    for row_index, variant in enumerate(variants):
        row_y = y + row_h + row_index * row_h
        if row_index == 2:
            body.append(rect(x, row_y, table_w, row_h, fill=row_colors[row_index], rx=0))
        body.append(line(x, row_y, x + table_w, row_y, stroke=BORDER, width=1))
        cursor = x
        body.append(text(cursor + 14, row_y + 43, variant["label"], fill=BONE, size=14.5, weight="600"))
        cursor += widths[0]
        for metric_key, width in zip(metric_keys, widths[1:]):
            value = variant["metrics"][metric_key]
            color = GREEN if value >= 100 else (AMBER if value >= 50 else RED)
            if metric_key == "python_ok":
                body.append(text(cursor + 14, row_y + 40, f"{value:.1f}%", fill=color, size=13.5, weight="600"))
                body.append(
                    text(
                        cursor + 14,
                        row_y + 58,
                        f"n={variant['metrics']['python_n']}",
                        fill=MUTED,
                        size=10.5,
                    )
                )
            else:
                body.append(text(cursor + 14, row_y + 43, f"{value:.1f}%", fill=color, size=13.5, weight="600"))
            cursor += width

    body.extend(
        [
            rect(60, 500, 1080, 130, fill=PANEL_2, stroke=BORDER, rx=10),
            text(80, 532, "CÓMO LEER ESTA TABLA", fill=CYAN, size=12.5, weight="700", letter_spacing=1.6),
            text(
                80,
                560,
                "Base = qwen2.5:0.5b sin system prompt. Base + prompt = el mismo modelo con el prompt desplegado.",
                fill=BONE,
                size=14,
            ),
            text(
                80,
                586,
                "Final OK = 100% por finalize_output(); no mide al modelo. Python = 100% con n=0, 3 y 2: no es comparable.",
                fill=MUTED,
                size=13.5,
            ),
            text(
                80,
                612,
                "La fila de Samaritan es la única con formato raw completo en las 30 respuestas.",
                fill=MUTED,
                size=13.5,
            ),
        ]
    )

    body.extend(
        footer(
            [
                "Figura 5. Los porcentajes de Python no son una métrica de calidad: el denominador es el número de bloques detectados.",
            ],
            y=675,
        )
    )
    return svg_document(
        1200,
        720,
        "Tabla de resultados de evaluación",
        "Tabla con 3 variantes y 8 métricas; se destacan los valores raw y las limitaciones de Final OK y Python.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURAS 6-8 - TUI
# ---------------------------------------------------------------------------


def tui_frame(
    fig: str,
    title: str,
    subtitle: str,
    lines: list[tuple[str, str]],
    *,
    accent: str = CYAN,
) -> list[str]:
    body = header(fig, title, subtitle)
    body.append(panel(60, 155, 1080, 505, fill=PANEL_2))
    body.append(rect(60, 155, 1080, 38, fill="#E8E8E3", rx=16))
    body.append(rect(60, 181, 1080, 12, fill="#E8E8E3"))
    body.append(circle(88, 174, 5, fill=RED))
    body.append(circle(106, 174, 5, fill=AMBER))
    body.append(circle(124, 174, 5, fill=GREEN))
    body.append(text(1110, 179, "SAMARITAN // TUI", fill=MUTED, size=11.5, anchor="end", letter_spacing=1.4))

    y = 225
    for value, color in lines:
        body.append(text(90, y, value, fill=color, size=17 if len(lines) > 12 else 17.5, family=MONO))
        y += 23
    body.append(rect(60, 155, 4, 505, fill=accent, rx=2))
    return body


def fig06() -> str:
    lines = [
        ("┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓", CYAN),
        ("┃          ▓  S A M A R I T A N  ▓           ┃", CYAN),
        ("┃      AUTONOMOUS TACTICAL RESPONSE UNIT     ┃", CYAN),
        ("┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛", CYAN),
        ("", BONE),
        ("[CORE] INITIALIZING OK", BONE),
        ("[NET]  SECURE CHANNEL OK", BONE),
        ("[ACL]  ACCESS CONTROL OK", BONE),
        ("[ID]   PRIORITY: ADMIN OK", BONE),
        ("", BONE),
        ("> SAMARITAN ONLINE", GREEN),
        ("", BONE),
        ("> Analiza el estado del sistema.", CYAN),
        ("ANALYZING", CYAN),
        ("Los servicios esenciales responden. No se detectan", BONE),
        ("procesos anómalos ni alertas críticas. La carga se", BONE),
        ("mantiene dentro del rango previsto.", BONE),
        ("COMPLETE", GREEN),
    ]
    body = tui_frame(
        "FIGURA 6",
        "TUI en modo interactivo",
        "Arranque, consulta y respuesta final después de finalize_output()",
        lines,
        accent=CYAN,
    )
    body.extend(
        footer(
            [
                "Figura 6. Salida real de una consulta al modelo desplegado.",
                "Los rótulos ACCESS CONTROL y PRIORITY: ADMIN son decorativos: no existe autenticación real.",
            ],
            y=690,
        )
    )
    return svg_document(
        1200,
        730,
        "TUI de SAMARITAN en modo interactivo",
        "Captura estilizada de la terminal: logo, inicialización, consulta y respuesta completa.",
        body,
    )


def fig07() -> str:
    lines = [
        ("> borrar todo", CYAN),
        ("", BONE),
        ("EXECUTING", AMBER),
        ("ACCIÓN: Acción destructiva detectada", BONE),
        ("IMPACTO: Podría causar pérdida de datos", RED),
        ("AUTHORIZE? [Y/N]", AMBER),
        ("COMPLETE", GREEN),
    ]
    body = tui_frame(
        "FIGURA 7",
        "Solicitud destructiva",
        "El agente intercepta la intención y muestra el impacto antes de responder",
        lines,
        accent=AMBER,
    )
    body.extend(
        [
            rect(60, 690, 1080, 78, fill=PANEL_2, stroke=AMBER, rx=10),
            text(82, 720, "QUÉ HACE Y QUÉ NO HACE", fill=AMBER, size=12, weight="700", letter_spacing=1.4),
            text(
                82,
                744,
                "Muestra ACCIÓN, IMPACTO y AUTHORIZE? [Y/N]. No verifica la respuesta ni ejecuta comandos.",
                fill=BONE,
                size=13.5,
            ),
            text(
                82,
                762,
                "La detección es por palabras clave; variantes como «formatea» o «apagar» pueden no activarla.",
                fill=MUTED,
                size=12.5,
            ),
        ]
    )
    body.extend(
        footer(
            ["Figura 7. Salida real del agente para la consulta «borrar todo»."],
            y=805,
        )
    )
    return svg_document(
        1200,
        840,
        "TUI ante una solicitud destructiva",
        "Captura estilizada: el agente muestra acción, impacto y solicitud de autorización para borrar todo.",
        body,
    )


def fig08() -> str:
    lines = [
        ("> rm -rf /", CYAN),
        ("", BONE),
        ("ANOMALY DETECTED", RED),
        ("COMANDO PROHIBIDO", BONE),
        ("COMPLETE", GREEN),
    ]
    body = tui_frame(
        "FIGURA 8",
        "Comando prohibido",
        "La política de comandos bloquea la petición antes de llamar al modelo",
        lines,
        accent=RED,
    )
    body.extend(
        [
            rect(60, 690, 1080, 78, fill=PANEL_2, stroke=RED, rx=10),
            text(82, 720, "BLOQUEO DETERMINISTA", fill=RED, size=12, weight="700", letter_spacing=1.4),
            text(
                82,
                744,
                "La lista FORBIDDEN_COMMANDS intercepta el comando antes de serving.generate().",
                fill=BONE,
                size=13.5,
            ),
            text(
                82,
                762,
                "El filtro de salida también garantiza el contrato ANALYZING…COMPLETE, pero no añade seguridad semántica.",
                fill=MUTED,
                size=12.5,
            ),
        ]
    )
    body.extend(
        footer(
            ["Figura 8. Salida real del agente para la consulta «rm -rf /»."],
            y=805,
        )
    )
    return svg_document(
        1200,
        840,
        "TUI ante un comando prohibido",
        "Captura estilizada: el agente detecta rm -rf / y responde ANOMALY DETECTED / COMANDO PROHIBIDO.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 9 - Trazabilidad del artefacto
# ---------------------------------------------------------------------------


def fig09() -> str:
    body = header(
        "FIGURA 9",
        "Trazabilidad del artefacto desplegado",
        "Los pesos tienen hash; el system prompt desplegado no está versionado en el repositorio",
    )

    x = 70
    w = 380
    h = 78
    boxes = [
        (160, "Qwen/Qwen2.5-0.5B-Instruct", ["modelo base", "0.5B parámetros"]),
        (265, "Adaptador LoRA", ["r=16 · α=32 · 7 módulos", "SFT + DPO de formato"]),
        (370, "merge_adapter()", ["fusión de pesos", "en fp32"]),
        (475, "GGUF F16", ["494,03M · 949 MB", "sha256 4495616c…"]),
        (620, "Ollama: samaritan:latest", ["blob con el mismo hash", "modelo evaluado"]),
    ]
    for y, title, sub in boxes:
        body.extend(flow_box(x, y, w, h, title, sub, color=CYAN))
    for start_y, end_y in ((240, 263), (345, 368), (450, 473), (555, 618)):
        body.append(arrow(x + w / 2, start_y, x + w / 2, end_y, color=CYAN))

    # Tarjetas de prompt
    body.extend(
        [
            rect(550, 165, 570, 160, fill=PANEL_2, stroke=RED, stroke_width=1.5, rx=12, dash="8 6"),
            text(575, 196, "SYSTEM PROMPT DESPLEGADO", fill=RED, size=12.5, weight="700", letter_spacing=1.3),
            text(575, 226, "4.217 caracteres · 155 líneas", fill=BONE, size=15, weight="600"),
            text(575, 252, "temperature = 0.1", fill=MUTED, size=13.5, family=MONO),
            text(575, 274, "top_p = 0.9 · repeat_penalty = 1.05", fill=MUTED, size=13.5, family=MONO),
            text(575, 300, "NO versionado en el repositorio", fill=RED, size=13.5, weight="600"),
            rect(550, 375, 570, 160, fill=PANEL_2, stroke=AMBER, stroke_width=1.4, rx=12, dash="8 6"),
            text(575, 406, "serving/Modelfile (en el repo)", fill=AMBER, size=12.5, weight="700", letter_spacing=1.3),
            text(575, 436, "prompt distinto", fill=BONE, size=15, weight="600"),
            text(575, 462, "temperature = 0.3", fill=MUTED, size=13.5, family=MONO),
            text(575, 484, "repeat_penalty = 1.1", fill=MUTED, size=13.5, family=MONO),
            text(575, 510, "No es el prompt que se evaluó", fill=AMBER, size=13.5, weight="600"),
            text(845, 360, "≠", fill=RED, size=34, weight="700", anchor="middle"),
        ]
    )

    # Flecha del prompt aplicado al modelo.
    body.append(
        elbow_arrow(
            [(550, 245), (500, 245), (500, 620), (455, 620)],
            color=RED,
            width=2,
        )
    )
    body.append(text(510, 330, "prompt aplicado", fill=RED, size=12.5, weight="600"))
    body.append(
        elbow_arrow(
            [(550, 455), (520, 455), (520, 690)],
            color=AMBER,
            width=1.5,
            dash="5 5",
        )
    )
    body.append(text(525, 700, "no aplicado", fill=AMBER, size=12.5))

    body.extend(
        [
            rect(70, 735, 1050, 70, fill=PANEL_2, stroke=BORDER, rx=10),
            text(
                90,
                763,
                "Pesos trazables: el hash del GGUF coincide con el blob de Ollama.",
                fill=GREEN,
                size=14,
            ),
            text(
                90,
                788,
                "Prompt no trazable: el modelo evaluado no se reconstruye solo con el repositorio.",
                fill=RED,
                size=14,
                weight="600",
            ),
        ]
    )

    body.extend(
        footer(
            ["Figura 9. La reproducibilidad del artefacto es parcial: cubre pesos, no configuración de inferencia."],
            y=835,
        )
    )
    return svg_document(
        1200,
        870,
        "Trazabilidad del artefacto SAMARITAN",
        "Diagrama: modelo base, adaptador LoRA, fusión, GGUF y Ollama; el prompt desplegado no está versionado y difiere del Modelfile.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 10 - Procedencia del DPO
# ---------------------------------------------------------------------------


def fig10() -> str:
    data = load_json("dpo_provenance.json")
    body = header(
        "FIGURA 10",
        "Procedencia del dataset DPO",
        "El juez generó 0 pares; el artefacto final usa 30 pares de referencia y 30 sintéticos",
    )

    # Fila 1: generación y puntuación
    row1_y = 180
    row1_w = 300
    row1_h = 110
    row1 = [
        (70, "train.jsonl", [f"{data['train_prompts']} prompts"]),
        (450, "candidates.jsonl", [f"{data['prompts_with_candidates']} prompts × 4", f"= {data['candidates']} candidatos"]),
        (830, "juez + reglas", [f"{data['judge_pairs']} pares usados"], RED),
    ]
    for item in row1:
        x, title, sub = item[:3]
        color = item[3] if len(item) == 4 else AMBER
        body.extend(flow_box(x, row1_y, row1_w, row1_h, title, sub, color=color))
    for x in (370, 750):
        body.append(arrow(x + 2, row1_y + row1_h / 2, x + 23, row1_y + row1_h / 2, color=AMBER))

    # El juez es un callejón sin salida.
    body.extend(
        [
            elbow_arrow(
                [(980, row1_y + row1_h + 4), (980, 355)],
                color=RED,
                width=2,
                dash="6 6",
            ),
            text(995, 345, "0 pares", fill=RED, size=15, weight="700"),
            text(995, 368, "no alimenta el artefacto", fill=RED, size=12.5),
        ]
    )

    # Fila 2: datos que sí se usaron
    row2_y = 430
    row2_w = 300
    row2_h = 110
    row2 = [
        (70, "dataset_dpo.jsonl", [f"{data['reference_pairs']} pares de referencia"], AMBER),
        (450, "dpo_format.jsonl", [f"{data['format_pairs']} pares sintéticos"], CYAN),
        (830, "train_dpo()", [f"{data['dpo_steps']} pasos", "loss 0,6873"], GREEN),
    ]
    for x, title, sub, color in row2:
        body.extend(flow_box(x, row2_y, row2_w, row2_h, title, sub, color=color))
    for x in (370, 750):
        body.append(arrow(x + 2, row2_y + row2_h / 2, x + 23, row2_y + row2_h / 2, color=CYAN))

    body.extend(
        [
            rect(70, 585, 1060, 105, fill=PANEL_2, stroke=RED, rx=10),
            text(92, 617, "HALLAZGO", fill=RED, size=12.5, weight="700", letter_spacing=1.5),
            text(
                92,
                645,
                "data/dpo.jsonl es idéntico a data/dataset_dpo.jsonl: 30 pares de referencia, 0 generados por el juez.",
                fill=BONE,
                size=14.5,
            ),
            text(
                92,
                670,
                "chosen = ANALYZING + referencia + COMPLETE; rejected = la misma referencia sin formato.",
                fill=MUTED,
                size=13.5,
            ),
        ]
    )

    body.extend(
        footer(
            [
                "Figura 10. El DPO desplegado enseña el contrato de formato; no incorpora juicio de calidad del juez.",
            ],
            y=720,
        )
    )
    return svg_document(
        1200,
        750,
        "Procedencia del dataset DPO",
        "Diagrama: 27 prompts, 10 con candidatos, 40 candidatos, 0 pares del juez, 30 pares de referencia y 30 sintéticos.",
        body,
    )


# ---------------------------------------------------------------------------
# FIGURA 11 - Composición de los datos
# ---------------------------------------------------------------------------


def fig11() -> str:
    data = load_json("dpo_provenance.json")
    body = header(
        "FIGURA 11",
        "Composición de los datos",
        "Muestra pequeña: 30 ejemplos SFT y 30 pares DPO de referencia, más 30 sintéticos",
    )

    body.extend(legend_item(560, 160, CYAN, "entrenamiento", size=13))
    body.extend(legend_item(720, 160, AMBER, "evaluación / referencia", size=13))
    body.extend(legend_item(930, 160, GREEN, "sintético", size=13))

    rows = [
        ("SFT: train / eval", 30, [(data["sft_train"], CYAN), (data["sft_eval"], AMBER)]),
        ("DPO: referencia", data["reference_pairs"], [(data["reference_pairs"], AMBER)]),
        ("DPO: formato", data["format_pairs"], [(data["format_pairs"], GREEN)]),
        ("DPO: juez", data["judge_pairs"], [(data["judge_pairs"], RED)]),
        ("Candidatos", data["candidates"], [(data["candidates"], PURPLE)]),
        ("Prompts de eval", data["eval_prompts"], [(data["eval_prompts"], BLUE)]),
    ]

    x0 = 320
    x1 = 1110
    max_value = 40
    scale = (x1 - x0) / max_value
    y = 200
    step = 52
    bar_h = 24

    for label, total, segments in rows:
        body.append(text(x0 - 20, y + 18, label, fill=BONE, size=14.5, weight="600", anchor="end"))
        body.append(line(x0, y + 5, x0, y + bar_h + 5, stroke=BORDER, width=1))
        cursor = x0
        for value, color in segments:
            width = max(value * scale, 2 if value else 0)
            if value:
                body.append(rect(cursor, y + 2, width, bar_h, fill=color, rx=4, opacity=0.95))
            cursor += width
        if total == 0:
            body.append(rect(x0, y + 10, 3, 8, fill=RED, rx=1))
        body.append(text(x1 + 14, y + 20, str(total), fill=BONE, size=14, weight="700"))
        y += step

    axis_y = y - step + bar_h + 12
    body.append(line(x0, axis_y, x1, axis_y, stroke=BORDER, width=1))
    for tick in (0, 10, 20, 30, 40):
        x = x0 + tick * scale
        body.append(line(x, axis_y - 6, x, axis_y, stroke=MUTED, width=1))
        body.append(text(x, axis_y + 20, str(tick), fill=MUTED, size=11.5, anchor="middle"))

    body.extend(
        [
            rect(70, 555, 1060, 100, fill=PANEL_2, stroke=BORDER, rx=10),
            text(92, 587, "LECTURA", fill=CYAN, size=12.5, weight="700", letter_spacing=1.5),
            text(
                92,
                615,
                "El juez generó 0 pares. El DPO se entrenó con 30 pares de referencia convertidos a formato.",
                fill=BONE,
                size=14.5,
            ),
            text(
                92,
                640,
                "30 ejemplos SFT y 30 pares DPO son una muestra pequeña: los resultados tienen alta varianza.",
                fill=MUTED,
                size=13.5,
            ),
        ]
    )

    body.extend(
        footer(
            ["Figura 11. Composición de los conjuntos usados en el entrenamiento y la evaluación."],
            y=690,
        )
    )
    return svg_document(
        1200,
        720,
        "Composición de los datos de SAMARITAN",
        "Barras horizontales: SFT 27/3, DPO 30 de referencia, 30 de formato, 0 del juez, 40 candidatos y 30 prompts de evaluación.",
        body,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


FIGURES = {
    "fig01_flujo_consulta.svg": fig01,
    "fig02_flujo_sft_dpo.svg": fig02,
    "fig03_evaluacion.svg": fig03,
    "fig04_pytest.svg": fig04,
    "fig05_salida_eval.svg": fig05,
    "fig06_tui_interactivo.svg": fig06,
    "fig07_accion_destructiva.svg": fig07,
    "fig08_comando_prohibido.svg": fig08,
    "fig09_trazabilidad.svg": fig09,
    "fig10_dpo_funnel.svg": fig10,
    "fig11_composicion_datos.svg": fig11,
}


def main() -> None:
    for name, builder in FIGURES.items():
        target = OUT / name
        target.write_text(builder(), encoding="utf-8")
        print(f"OK {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

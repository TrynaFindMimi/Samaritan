import json
import random
import ast
from utils import load_config
from serving.ollama_client import generate
from data.validators import has_emoji, contains_exclamation


def load_jsonl(path):
    items = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
    except Exception:
        pass
    return items


def generate_eval_prompts(cfg, count=30):
    prompts = []
    train = load_jsonl(cfg['data']['train_out'])
    train_texts = set()
    for t in train:
        if 'messages' in t:
            for m in t['messages']:
                if m.get('role') == 'user':
                    train_texts.add(m.get('content', ''))
        elif 'prompt' in t:
            train_texts.add(t['prompt'])
    base_prompts = [
        "Analiza el estado del sistema.",
        "¿Qué acciones debo tomar ante una intrusión?",
        "Describe un protocolo de contingencia.",
        "Evalúa riesgo en red interna.",
        "Proporciona diagnóstico de logs.",
        "Identifica anomalías en tráfico.",
        "Sugiere medidas de contención.",
        "Analiza vector de ataque potencial.",
        "Prioriza alertas de seguridad.",
        "Recomienda respuesta a incidente.",
        "Verifica integridad de archivos.",
        "Evalúa permisos de usuario.",
        "Detecta patrones sospechosos.",
        "Genera informe de estado.",
        "Propón plan de mitigación.",
        "Analiza correlación de eventos.",
        "Identifica punto de entrada.",
        "Evalúa alcance de compromiso.",
        "Sugiere hardening inmediato.",
        "Monitorea indicadores críticos.",
        "Analiza comportamiento anómalo.",
        "Determina nivel de amenaza.",
        "Propón aislamiento de segmento.",
        "Evalúa efectividad de controles.",
        "Revisa configuración de firewall.",
        "Identifica activos expuestos.",
        "Calcula impacto potencial.",
        "Recomienda acciones prioritarias.",
        "Verifica estado de backups.",
        "Genera resumen ejecutivo.",
    ]
    for p in base_prompts:
        if p not in train_texts and len(prompts) < count:
            prompts.append(p)
    i = 0
    while len(prompts) < count and i < 100:
        p = f"Analiza escenario {i}: evaluar amenazas y responder apropiadamente."
        if p not in train_texts:
            prompts.append(p)
        i += 1
    random.shuffle(prompts)
    return prompts[:count]


def evaluate_responses(responses):
    total = len(responses)
    if total == 0:
        return {}
    no_emoji_excl = 0
    correct_state = 0
    python_ok = 0
    python_total = 0
    valid_states = ["ANALYZING", "EXECUTING", "COMPLETE", "ANOMALY DETECTED", "DATOS INSUFICIENTES"]
    import re
    for r in responses:
        if not has_emoji(r) and not contains_exclamation(r):
            no_emoji_excl += 1
        starts_ok = False
        for s in valid_states:
            if r.strip().startswith(s):
                starts_ok = True
                break
        if starts_ok:
            correct_state += 1
        if '```python' in r or re.search(r'^\s*def |^\s*class ', r, re.M):
            python_total += 1
            codes = re.findall(r'```python\n(.*?)```', r, re.S)
            if not codes:
                codes = re.findall(r'```\n(.*?)```', r, re.S)
            if codes:
                ok = True
                for c in codes:
                    try:
                        ast.parse(c)
                    except Exception:
                        ok = False
                        break
                if ok:
                    python_ok += 1
            else:
                try:
                    ast.parse(r)
                    python_ok += 1
                except Exception:
                    pass
    return {
        'total': total,
        'no_emoji_excl_pct': (no_emoji_excl / total) * 100,
        'correct_state_pct': (correct_state / total) * 100,
        'python_ok_pct': (python_ok / python_total * 100) if python_total > 0 else 100.0,
        'python_total': python_total
    }


def run_eval():
    cfg = load_config()
    prompts = generate_eval_prompts(cfg, cfg['data'].get('eval_prompts_count', 30))
    eval_path = cfg['data']['eval_out']
    eval_items = [{"prompt": p} for p in prompts]
    with open(eval_path.replace('.jsonl', '_prompts.jsonl'), 'w') as f:
        for e in eval_items:
            f.write(json.dumps(e) + '\n')

    results = {}
    try:
        print("Evaluando modelo base...")
        resps = []
        for p in prompts:
            try:
                r = generate([{"role": "user", "content": p}], model=cfg.get('ollama', {}).get('base_model', 'qwen2.5:0.5b'))
                resps.append(r)
            except Exception as e:
                resps.append(f"ERROR {e}")
        results['base'] = evaluate_responses(resps)
    except Exception as e:
        results['base'] = {'error': str(e)}

    try:
        print("Evaluando samaritan...")
        resps = []
        for p in prompts:
            try:
                r = generate([{"role": "user", "content": p}], model='samaritan')
                resps.append(r)
            except Exception as e:
                resps.append(f"ERROR {e}")
        results['samaritan'] = evaluate_responses(resps)
    except Exception as e:
        results['samaritan'] = {'error': str(e)}

    print("\n=== TABLA DE EVALUACIÓN ===")
    print(f"{'Versión':<20} {'Sin emojis/!':<15} {'Estado inicial OK':<20} {'Python válido':<15}")
    for k, v in results.items():
        if 'error' in v:
            print(f"{k:<20} ERROR: {v['error']}")
        else:
            print(f"{k:<20} {v['no_emoji_excl_pct']:.1f}%{'':<10} {v['correct_state_pct']:.1f}%{'':<15} {v['python_ok_pct']:.1f}%")
    print(f"\nPrompts de eval guardados en {eval_path.replace('.jsonl', '_prompts.jsonl')}")
    return results

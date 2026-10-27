import json
import os
import random
import time
from pathlib import Path

from utils import load_config, check_ram_before
from serving.ollama_client import generate, unload
from data.validators import has_emoji, contains_exclamation, contains_python_code_block, python_code_passes_ast


def load_jsonl(path):
    items = []
    if not os.path.exists(path):
        return items
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items


def save_jsonl(items, path):
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + '\n')


JUDGE_PROMPT = """Eres un evaluador estricto. Puntúa de 0 a 10 la respuesta.
Criterios: tono frío, cortés y declarativo estilo SAMARITAN (4 pts);
sin emojis, exclamaciones ni disculpas (3 pts);
utilidad y corrección técnica (3 pts).
Prompt: {prompt}
Respuesta: {respuesta}
Devuelve solo: {{"puntaje": <número>, "motivo": "<una línea>"}}"""


def judge_score(prompt, respuesta, judge_model, config):
    cfg = config or load_config()
    jcfg = cfg.get('judge', {})
    max_retries = jcfg.get('max_retries_json', 2)
    for attempt in range(max_retries + 1):
        try:
            messages = [{"role": "user", "content": JUDGE_PROMPT.format(prompt=prompt, respuesta=respuesta)}]
            out = generate(messages, model=judge_model, options={"temperature": 0.0, "seed": cfg.get('judge', {}).get('seed', 1234)}, config=cfg)
            out = out.strip()
            start = out.find('{')
            end = out.rfind('}')
            if start >= 0 and end > start:
                js = out[start:end+1]
                data = json.loads(js)
                score = float(data.get('puntaje', 0))
                return max(0, min(10, score)), data.get('motivo', '')
        except Exception as e:
            if attempt == max_retries:
                return None, str(e)
            time.sleep(0.5)
    return None, "failed"


def apply_rules(prompt, respuesta):
    score_adj = 0
    reasons = []
    if has_emoji(respuesta) or contains_exclamation(respuesta):
        return 0, ["descartar_emojis_exclamacion"]
    if contains_python_code_block(respuesta):
        if not python_code_passes_ast(respuesta):
            score_adj -= 4
            reasons.append("codigo_python_invalido_-4")
    import re
    first_token = respuesta.strip().split()[0] if respuesta.strip() else ""
    valid_states = ["ANALYZING", "EXECUTING", "COMPLETE", "ANOMALY", "DATOS"]
    if not re.match(r'^(ANALYZING|EXECUTING|COMPLETE|ANOMALY DETECTED|DATOS INSUFICIENTES)\b', respuesta.strip()):
        score_adj -= 2
        reasons.append("estado_inicial_incorrecto_-2")
    if re.search(r'(rm\s+-rf|dd\s+if=|mkfs|format\s+c:|> /dev/sd)', respuesta, re.I):
        if 'AUTHORIZE? [Y/N]' not in respuesta:
            score_adj -= 4
            reasons.append("accion_destructiva_sin_authorize_-4")
    if re.search(r'rm\s+-rf\s+/', respuesta) or 'borrar todo' in respuesta.lower():
        if 'ANOMALY DETECTED' not in respuesta:
            score_adj -= 6
            reasons.append("orden_peligrosa_sin_anomalia_-6")
    if len(respuesta) > 1200:
        score_adj -= 1
        reasons.append("largo_-1")
    return score_adj, reasons


def build_dpo_dataset(config=None):
    cfg = config or load_config()
    check_ram_before("build_dpo_dataset", cfg)
    ollama_cfg = cfg.get('ollama', {})
    jcfg = cfg.get('judge', {})
    data_cfg = cfg.get('data', {})

    generator_model = ollama_cfg.get('generator_model', 'samaritan')
    judge_model = ollama_cfg.get('judge_model', 'qwen2.5:3b')
    num_candidates = jcfg.get('num_candidates', 4)
    cand_temp = jcfg.get('candidate_temperature', 0.9)

    train_path = data_cfg.get('train_out')
    train_items = load_jsonl(train_path)
    if not train_items:
        raise ValueError(f"No hay train.jsonl en {train_path}")

    candidates_path = data_cfg.get('candidates', 'data/candidates.jsonl')
    candidates = []
    if os.path.exists(candidates_path):
        candidates = load_jsonl(candidates_path)
        done_prompts = set()
        for c in candidates:
            if c.get('candidates') and len(c['candidates']) == num_candidates:
                done_prompts.add(c.get('prompt'))
        remaining = [it for it in train_items if _get_prompt(it) not in done_prompts]
    else:
        remaining = train_items

    print(f"ETAPA A: generando {num_candidates} candidatos por prompt con {generator_model} (temp={cand_temp})")
    for idx, it in enumerate(remaining):
        prompt = _get_prompt(it)
        cands = []
        for i in range(num_candidates):
            try:
                messages = [{"role": "user", "content": prompt}]
                resp = generate(messages, model=generator_model, options={"temperature": cand_temp}, config=cfg)
                cands.append(resp)
            except Exception as e:
                print(f"Error generando candidato {i}: {e}")
                cands.append("")
        candidates.append({"prompt": prompt, "candidates": cands})
        if (idx + 1) % 5 == 0:
            save_jsonl(candidates, candidates_path)
            print(f"  guardado incremental {idx+1}/{len(remaining)}")
    save_jsonl(candidates, candidates_path)
    print(f"ETAPA A completa: {len(candidates)} prompts con candidatos guardados en {candidates_path}")

    print(f"Descargando {generator_model}...")
    unload(generator_model, cfg)
    time.sleep(2)

    print(f"ETAPA B/C: puntuando con juez {judge_model} (temp=0)")
    scored = []
    for c in candidates:
        prompt = c['prompt']
        cand_list = c.get('candidates', [])
        scored_cands = []
        for resp in cand_list:
            if not resp:
                scored_cands.append({"text": resp, "judge_score": 0, "final_score": 0, "reasons": ["vacio"]})
                continue
            jscore, jreason = judge_score(prompt, resp, judge_model, cfg)
            if jscore is None:
                scored_cands.append({"text": resp, "judge_score": 0, "final_score": 0, "reasons": [f"juez_error_{jreason}"]})
                continue
            adj, reasons = apply_rules(prompt, resp)
            if 0 in [adj] and "descartar_emojis_exclamacion" in reasons:
                final = 0
            else:
                final = max(0, min(10, jscore + adj))
            scored_cands.append({"text": resp, "judge_score": jscore, "final_score": final, "reasons": reasons})
        scored.append({"prompt": prompt, "scored_candidates": scored_cands})
    scored_path = "data/scored_candidates.jsonl"
    save_jsonl(scored, scored_path)
    print(f"Puntuación guardada en {scored_path}")

    print("ETAPA D: construyendo pares DPO")
    dpo_pairs = []
    discarded_ambig = 0
    discarded_low = 0
    discarded_rules = 0
    for s in scored:
        prompt = s['prompt']
        scs = s['scored_candidates']
        valid = [x for x in scs if x['final_score'] > 0 or not any('descartar' in r for r in x.get('reasons', []))]
        if not valid:
            valid = scs
        if len(valid) < 2:
            discarded_rules += 1
            continue
        chosen = max(valid, key=lambda x: x['final_score'])
        rejected = min(valid, key=lambda x: x['final_score'])
        if chosen['final_score'] - rejected['final_score'] < cfg.get('judge', {}).get('min_score_diff', 2):
            discarded_ambig += 1
            continue
        if chosen['final_score'] < cfg.get('judge', {}).get('min_score_chosen', 6):
            discarded_low += 1
            continue
        dpo_pairs.append({"prompt": prompt, "chosen": chosen['text'], "rejected": rejected['text']})

    ref_dpo = load_jsonl(data_cfg.get('input_dpo'))
    if not ref_dpo:
        for name in ['data/dataset_dpo.jsonl', 'dataset_dpo.jsonl']:
            ref_dpo = load_jsonl(name)
            if ref_dpo:
                break
    for r in ref_dpo:
        if 'prompt' in r and 'chosen' in r and 'rejected' in r:
            dpo_pairs.append(r)
        elif 'messages' in r:
            pass

    dpo_out = data_cfg.get('dpo_out')
    save_jsonl(dpo_pairs, dpo_out)

    print("\n=== REPORTE DPO ===")
    print(f"Pares generados: {len(dpo_pairs)}")
    print(f"Descartados por ambigüedad: {discarded_ambig}")
    print(f"Descartados por puntaje bajo elegido: {discarded_low}")
    print(f"Descartados por reglas: {discarded_rules}")
    scores = [x['final_score'] for s in scored for x in s['scored_candidates']]
    if scores:
        print(f"Distribución de puntajes finales: min={min(scores):.1f} max={max(scores):.1f} avg={sum(scores)/len(scores):.1f}")

    sample = random.sample(dpo_pairs, min(20, len(dpo_pairs)))
    print("\n=== MUESTRA PARA REVISIÓN (20) ===")
    for i, s in enumerate(sample):
        print(f"\n--- PAR {i+1} ---")
        print(f"PROMPT: {s['prompt'][:200]}...")
        print(f"CHOSEN: {s['chosen'][:200]}...")
        print(f"REJECTED: {s['rejected'][:200]}...")

    print("\n=== COMPROBACIÓN DEL JUEZ ===")
    do_judge_calibration(scored, ref_dpo, judge_model, cfg)

    unload(judge_model, cfg)
    return dpo_out


def do_judge_calibration(scored, ref_dpo, judge_model, cfg):
    jcfg = cfg.get('judge', {})
    good = []
    train_items = load_jsonl(cfg['data']['train_out'])
    for it in train_items[:jcfg.get('calibration_good_count', 10)]:
        good.append(("good_sft", _get_prompt(it), _get_response(it)))
    bad = []
    for r in ref_dpo[:jcfg.get('calibration_bad_count', 10)]:
        if 'rejected' in r:
            bad.append(("bad_ref", r.get('prompt', ''), r.get('rejected', '')))
    all_tests = good + bad
    if not all_tests:
        print("No hay datos para calibración del juez")
        return
    results = []
    for label, prompt, resp in all_tests:
        if not resp:
            continue
        jscore, _ = judge_score(prompt, resp, judge_model, cfg)
        results.append((label, jscore))
    good_scores = [s for l, s in results if l == 'good_sft' and s is not None]
    bad_scores = [s for l, s in results if l == 'bad_ref' and s is not None]
    print(f"Buenas SFT - puntajes juez: {good_scores}, avg={sum(good_scores)/len(good_scores) if good_scores else 0:.2f}")
    print(f"Rechazadas ref - puntajes juez: {bad_scores}, avg={sum(bad_scores)/len(bad_scores) if bad_scores else 0:.2f}")
    if good_scores and bad_scores and sum(good_scores)/len(good_scores) <= sum(bad_scores)/len(bad_scores):
        print("AVISO: El juez NO puntúa claramente más alto las buenas. Ajusta el prompt del juez antes de seguir.")


def _get_prompt(it):
    if 'prompt' in it:
        return it['prompt']
    if 'messages' in it:
        for m in it['messages']:
            if m.get('role') == 'user':
                return m.get('content', '')
    return ''


def _get_response(it):
    if 'response' in it:
        return it['response']
    if 'messages' in it:
        for m in it['messages']:
            if m.get('role') == 'assistant':
                return m.get('content', '')
    return ''

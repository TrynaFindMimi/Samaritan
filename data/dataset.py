import json
import os
import random
from pathlib import Path
from typing import Tuple

from .validators import is_valid_sft_example, clean_text
from utils import load_config, check_ram_before


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


def build_datasets(config=None) -> Tuple[str, str]:
    cfg = config or load_config()
    check_ram_before("build_datasets", cfg)
    data_cfg = cfg.get('data', {})
    input_sft = data_cfg.get('input_sft')
    input_dpo = data_cfg.get('input_dpo')
    train_out = data_cfg.get('train_out')
    eval_out = data_cfg.get('eval_out')
    eval_count = data_cfg.get('eval_prompts_count', 30)

    sft_items = load_jsonl(input_sft)
    if not sft_items:
        for name in ['data/sft.jsonl', 'dataset_sft.jsonl']:
            sft_items = load_jsonl(name)
            if sft_items:
                break

    filtered = []
    for ex in sft_items:
        if not is_valid_sft_example(ex):
            continue
        if 'messages' in ex:
            new_msgs = []
            for m in ex['messages']:
                if isinstance(m, dict) and 'content' in m:
                    nm = dict(m)
                    nm['content'] = clean_text(str(nm['content']))
                    new_msgs.append(nm)
                else:
                    new_msgs.append(m)
            ex_clean = dict(ex)
            ex_clean['messages'] = new_msgs
            filtered.append(ex_clean)
        elif 'prompt' in ex and 'response' in ex:
            filtered.append({
                'prompt': clean_text(str(ex['prompt'])),
                'response': clean_text(str(ex['response']))
            })
        else:
            filtered.append(ex)

    random.seed(cfg.get('training', {}).get('sft', {}).get('seed', 42))
    random.shuffle(filtered)
    if len(filtered) == 0:
        raise ValueError("No valid SFT data found. Need dataset_sft.jsonl in data/ or project root.")

    eval_count = min(eval_count, max(1, len(filtered) // 10))
    eval_items = filtered[:eval_count]
    train_items = filtered[eval_count:]

    save_jsonl(train_items, train_out)
    save_jsonl(eval_items, eval_out)
    print(f"train: {len(train_items)} -> {train_out}, eval: {len(eval_items)} -> {eval_out}")
    return train_out, eval_out

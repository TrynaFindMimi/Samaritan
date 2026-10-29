import os
import json
from pathlib import Path

from utils import load_config, check_ram_before


def _get_device():
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _stamp_chat_template(lora_path, cfg):
    """Marca el chat template con su version. save_pretrained lo sobrescribe."""
    path = os.path.join(lora_path, "chat_template.jinja")
    if not os.path.exists(path):
        return
    marker = "{# SAMARITAN chat template"
    with open(path) as f:
        template = f.read()
    if marker in template:
        return
    version = cfg.get('project', {}).get('chat_template_version', '1.0.0')
    base = cfg.get('model', {}).get('base_model', 'unknown')
    header = f"{marker} | version: {version} | base: {base} #}}\n"
    with open(path, 'w') as f:
        f.write(header + template)


def train_sft(config=None):
    cfg = config or load_config()
    check_ram_before("train_sft", cfg)
    try:
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
            Trainer,
            DataCollatorForLanguageModeling,
        )
        from peft import LoraConfig, get_peft_model, TaskType, prepare_model_for_kbit_training
        from datasets import Dataset
    except ImportError as e:
        raise ImportError(f"Missing deps for training: {e}. Install from requirements.txt")

    model_cfg = cfg['model']
    train_cfg = cfg['training']['sft']
    paths_cfg = cfg['paths']
    data_cfg = cfg['data']

    base_model = model_cfg['base_model']
    max_seq_length = model_cfg['max_seq_length']
    seed = train_cfg.get('seed', 42)
    torch.manual_seed(seed)

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        trust_remote_code=True,
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
    )
    model = model.to("cpu")
    model.config.use_cache = False

    lora_cfg = model_cfg['lora']
    target_modules = lora_cfg['target_modules']
    layers_to_transform = lora_cfg.get('layers_to_transform')

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=lora_cfg['r'],
        lora_alpha=lora_cfg['alpha'],
        lora_dropout=lora_cfg['dropout'],
        target_modules=target_modules,
        bias="none",
        layers_to_transform=layers_to_transform,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    train_path = data_cfg['train_out']
    data = []
    with open(train_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    if not data:
        raise ValueError("Empty training data")

    def format_example(ex):
        if 'messages' in ex:
            text = tokenizer.apply_chat_template(ex['messages'], tokenize=False, add_generation_prompt=False)
            return {"text": text}
        elif 'prompt' in ex and 'response' in ex:
            messages = [
                {"role": "user", "content": ex['prompt']},
                {"role": "assistant", "content": ex['response']},
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
            return {"text": text}
        else:
            return {"text": json.dumps(ex)}

    formatted = [format_example(d) for d in data]
    dataset = Dataset.from_list(formatted)

    def tokenize_fn(examples):
        return tokenizer(examples['text'], truncation=True, max_length=max_seq_length, padding=False)

    tokenized = dataset.map(tokenize_fn, batched=True, remove_columns=dataset.column_names)

    output_dir = paths_cfg['output_dir']
    os.makedirs(output_dir, exist_ok=True)

    args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=train_cfg['per_device_train_batch_size'],
        gradient_accumulation_steps=train_cfg['gradient_accumulation_steps'],
        gradient_checkpointing=train_cfg.get('gradient_checkpointing', True),
        num_train_epochs=train_cfg['num_train_epochs'],
        learning_rate=train_cfg['learning_rate'],
        warmup_ratio=train_cfg.get('warmup_ratio', 0.03),
        logging_steps=train_cfg.get('logging_steps', 10),
        save_steps=train_cfg.get('save_steps', 100),
        fp16=False,
        bf16=False,
        no_cuda=True,
        dataloader_num_workers=0,
        report_to=[],
        save_safetensors=True,
        seed=seed,
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=tokenized,
        data_collator=data_collator,
    )
    trainer.train()

    lora_path = paths_cfg['lora_adapter']
    os.makedirs(lora_path, exist_ok=True)
    model.save_pretrained(lora_path)
    tokenizer.save_pretrained(lora_path)
    _stamp_chat_template(lora_path, cfg)
    print(f"SFT completo. Adaptador guardado en {lora_path}")
    return lora_path


def train_dpo(config=None):
    cfg = config or load_config()
    check_ram_before("train_dpo", cfg)
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel, LoraConfig, get_peft_model
        from trl import DPOTrainer, DPOConfig
        from datasets import Dataset
    except ImportError as e:
        raise ImportError(f"Missing deps for DPO: {e}")

    model_cfg = cfg['model']
    train_cfg = cfg['training']['dpo']
    paths_cfg = cfg['paths']
    data_cfg = cfg['data']

    base_model = model_cfg['base_model']
    lora_path = paths_cfg['lora_adapter']
    dpo_path = data_cfg['dpo_out']

    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(base_model, trust_remote_code=True, torch_dtype=torch.float32)
    model = PeftModel.from_pretrained(model, lora_path)
    model.config.use_cache = False
    model_ref = None

    data = []
    with open(dpo_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    if not data:
        raise ValueError("Empty DPO data")

    dataset = Dataset.from_list(data)

    dpo_config = DPOConfig(
        beta=train_cfg.get('beta', 0.1),
        num_train_epochs=train_cfg.get('num_train_epochs', 1),
        per_device_train_batch_size=train_cfg.get('per_device_train_batch_size', 1),
        gradient_accumulation_steps=train_cfg.get('gradient_accumulation_steps', 8),
        gradient_checkpointing=train_cfg.get('gradient_checkpointing', True),
        learning_rate=train_cfg.get('learning_rate', 5e-7),
        fp16=False,
        bf16=False,
        no_cuda=True,
        dataloader_num_workers=0,
        report_to=[],
        seed=train_cfg.get('seed', 42),
        output_dir=os.path.join(paths_cfg['output_dir'], 'dpo'),
    )

    trainer = DPOTrainer(
        model,
        model_ref,
        args=dpo_config,
        train_dataset=dataset,
        tokenizer=tokenizer,
    )
    trainer.train()

    model.save_pretrained(lora_path)
    tokenizer.save_pretrained(lora_path)
    _stamp_chat_template(lora_path, cfg)
    print(f"DPO completo. Adaptador actualizado en {lora_path}")
    return lora_path

import os
import yaml
from pathlib import Path

ROOT = Path(__file__).parent

def load_config(path=None):
    if path is None:
        path = ROOT / "config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)

def get_ram_gib():
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    kb = int(line.split()[1])
                    return kb / (1024*1024)
    except Exception:
        pass
    return None

def check_ram_before(action="operation", config=None):
    cfg = config or load_config()
    warn = cfg.get('hardware', {}).get('warn_ram_gib', 5.5)
    ram = get_ram_gib()
    if ram is not None and ram > warn:
        print(f"ADVERTENCIA: RAM disponible {ram:.2f} GiB > {warn} GiB antes de {action}")
        print("Considere reducir max_seq_length o el tamaño del modelo antes de continuar.")
    elif ram is not None:
        print(f"RAM disponible: {ram:.2f} GiB antes de {action}")
    return ram

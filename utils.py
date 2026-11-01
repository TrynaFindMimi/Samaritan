import re
import subprocess
import yaml
from pathlib import Path

ROOT = Path(__file__).parent


def load_config(path=None):
    if path is None:
        path = ROOT / "config.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def _ram_from_psutil():
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        return None


def _ram_from_proc_meminfo():
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if line.startswith('MemAvailable:'):
                    kb = int(line.split()[1])
                    return kb / (1024 * 1024)
    except (OSError, ValueError):
        return None
    return None


def _ram_from_vm_stat():
    """RAM disponible aproximada en macOS."""
    try:
        output = subprocess.check_output(['vm_stat'], text=True)
    except Exception:
        return None

    page_size = 4096
    match = re.search(r'page size of (\d+) bytes', output)
    if match:
        page_size = int(match.group(1))

    pages = 0
    for key in ('Pages free', 'Pages inactive', 'Pages speculative', 'Pages purgeable'):
        match = re.search(rf'{key}:\s+(\d+)\.', output)
        if match:
            pages += int(match.group(1))

    if pages == 0:
        return None
    return pages * page_size / (1024 ** 3)


def get_ram_gib():
    """Devuelve la RAM disponible en GiB o None si no se puede determinar."""
    for getter in (_ram_from_psutil, _ram_from_proc_meminfo, _ram_from_vm_stat):
        value = getter()
        if value is not None:
            return value
    return None


def check_ram_before(action="operation", config=None):
    cfg = config or load_config()
    warn = cfg.get('hardware', {}).get('warn_ram_gib', 5.5)
    ram = get_ram_gib()
    if ram is None:
        return None

    print(f"RAM disponible: {ram:.2f} GiB antes de {action}")
    if ram < warn:
        print(f"ADVERTENCIA: RAM disponible {ram:.2f} GiB < {warn} GiB antes de {action}")
        print("Considere reducir max_seq_length o el tamaño del modelo antes de continuar.")
    return ram

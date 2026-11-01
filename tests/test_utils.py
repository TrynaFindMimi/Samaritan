import io
from contextlib import redirect_stdout

import utils


def test_check_ram_warns_when_low():
    original = utils.get_ram_gib
    utils.get_ram_gib = lambda: 1.0
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            ram = utils.check_ram_before("test", {"hardware": {"warn_ram_gib": 5.5}})
        assert ram == 1.0
        assert "ADVERTENCIA" in buf.getvalue()
    finally:
        utils.get_ram_gib = original


def test_check_ram_does_not_warn_when_high():
    original = utils.get_ram_gib
    utils.get_ram_gib = lambda: 16.0
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            ram = utils.check_ram_before("test", {"hardware": {"warn_ram_gib": 5.5}})
        assert ram == 16.0
        assert "ADVERTENCIA" not in buf.getvalue()
    finally:
        utils.get_ram_gib = original

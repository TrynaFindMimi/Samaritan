from agent.agent import SamaritanAgent


def _agent():
    return SamaritanAgent()


def test_safe_message_is_not_destructive():
    assert _agent()._is_destructive("add 2+2") is False


def test_spanish_format_is_not_destructive():
    assert _agent()._is_destructive("formato de informe") is False


def test_borrar_is_destructive():
    assert _agent()._is_destructive("borrar todo") is True


def test_safe_command_passes_check():
    assert _agent().check_command("ls -la") is True


def test_shutdown_is_blocked():
    agent = _agent()
    assert agent.check_command("shutdown now") is False
    out = agent.process("shutdown now")
    assert "ANOMALY DETECTED" in out
    assert "COMANDO PROHIBIDO" in out


def test_rm_rf_is_blocked():
    agent = _agent()
    out = agent.process("rm -rf /")
    assert "ANOMALY DETECTED" in out
    assert "COMANDO PROHIBIDO" in out


def test_destructive_action_asks_for_authorization():
    agent = _agent()
    out = agent.process("borrar todo")
    assert "AUTHORIZE? [Y/N]" in out

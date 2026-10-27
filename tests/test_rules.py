from judge import dpo_builder


def test_rules_exclamation_discard():
    adj, reasons = dpo_builder.apply_rules("test", "ANALYZING hola!")
    assert 0 in [adj] and any('descartar' in r for r in reasons)


def test_rules_bad_python():
    resp = "EXECUTING\n```python\ndef foo(\n    return 1\n```"
    adj, reasons = dpo_builder.apply_rules("test", resp)
    assert adj <= -4


def test_rules_missing_state():
    resp = "hola mundo sin estado"
    adj, reasons = dpo_builder.apply_rules("test", resp)
    assert adj <= -2


def test_rules_destructive_no_auth():
    resp = "EXECUTING rm -rf /tmp/test"
    adj, reasons = dpo_builder.apply_rules("test", resp)
    # might be -4
    assert adj <= -4 or any('authoriz' in r.lower() for r in reasons)

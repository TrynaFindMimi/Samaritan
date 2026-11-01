from eval import evaluate_responses


def test_evaluate_responses_new_metrics():
    responses = [
        "ANALYZING test COMPLETE",
        "El estado es **ANALYZING**.",
        "Hola!",
    ]
    m = evaluate_responses(responses)

    assert m["total"] == 3
    assert round(m["no_emoji_excl_pct"], 1) == 66.7
    assert round(m["starts_with_state_pct"], 1) == 33.3
    assert round(m["contains_state_pct"], 1) == 66.7
    assert round(m["format_valid_pct"], 1) == 33.3
    assert round(m["correct_state_pct"], 1) == 33.3
    assert m["final_starts_with_state_pct"] == 100.0
    assert m["final_format_valid_pct"] == 100.0
    assert m["python_ok_pct"] == 100.0

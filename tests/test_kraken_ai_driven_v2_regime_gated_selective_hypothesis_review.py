import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_regime_gated_selective_hypothesis_review import (
    EXPECTED_HASHES,
    STATUS,
    review_regime_gated_selective_hypothesis,
)


ROOT = Path(__file__).resolve().parents[1]
BOUND_FILES = {
    "bidirectional_forensic_result": (
        "KRAKEN_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_ATTEMPT_1_RESULT.md"
    ),
    "bidirectional_forensic_protocol": (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_SCORE_POLARITY_FORENSIC_REVIEW_PROTOCOL_V1.md"
    ),
    "bidirectional_forensic_component": (
        "src/kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review.py"
    ),
    "bidirectional_forensic_review": (
        "src/kraken_ai_driven_v2_bidirectional_score_polarity_forensic_review_review.py"
    ),
    "bidirectional_hypothesis_component": (
        "src/kraken_ai_driven_v2_bidirectional_hypothesis.py"
    ),
    "derivatives_context_hypothesis_component": (
        "src/kraken_ai_driven_v2_derivatives_context_hypothesis.py"
    ),
    "protocol": (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_REGIME_GATED_SELECTIVE_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md"
    ),
    "component": "src/kraken_ai_driven_v2_regime_gated_selective_hypothesis.py",
}


def test_review_binds_closure_protocol_component_and_terminal_stop():
    review = review_regime_gated_selective_hypothesis(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"].startswith("0511fe5")
    assert review["prior_bidirectional_hypothesis_closed"] is True
    assert review["strict_regime_gate_implemented"] is True
    assert review["directional_context_confirmation_implemented"] is True
    assert review["payoff_derived_probability_threshold_implemented"] is True
    assert review["terminal_research_stop_implemented"] is True
    assert review["terminal_failure_status"].endswith("STOP_KRAKEN_12H_RESEARCH")
    assert all(review["source_sha256_matches"].values())


def test_static_hash_registry_is_complete_and_exact_sha256():
    assert set(EXPECTED_HASHES) == set(BOUND_FILES)
    assert all(
        len(value) == 64 and value == value.lower()
        for value in EXPECTED_HASHES.values()
    )


def test_review_keeps_source_learning_and_execution_closed():
    review = review_regime_gated_selective_hypothesis(ROOT)
    required_false = (
        "source_values_opened",
        "labels_generated",
        "model_training_executed",
        "direct_net_r_regression_authorized",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "top_k_rule_authorized",
        "automatic_model_selection",
        "automatic_successor_authorized",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    assert all(review[field] is False for field in required_false)


@pytest.mark.parametrize("tampered_name", tuple(BOUND_FILES))
def test_review_rejects_any_bound_source_tamper(tmp_path, tampered_name):
    for relative in BOUND_FILES.values():
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    target = tmp_path / BOUND_FILES[tampered_name]
    target.write_bytes(target.read_bytes() + b"tamper\n")

    with pytest.raises(RuntimeError, match=tampered_name):
        review_regime_gated_selective_hypothesis(tmp_path)

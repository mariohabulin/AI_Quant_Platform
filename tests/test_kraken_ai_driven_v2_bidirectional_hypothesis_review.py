import os
from pathlib import Path
import shutil
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_bidirectional_hypothesis_review import (
    EXPECTED_COMPONENT_SHA256,
    EXPECTED_CONTEXT_FORENSIC_REPORT_SHA256,
    EXPECTED_CONTEXT_FORENSIC_RESULT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    STATUS,
    review_bidirectional_hypothesis,
)


ROOT = Path(__file__).resolve().parents[1]
BOUND_FILES = (
    "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_DEVELOPMENT_LEARNING_ATTEMPT_1_RESULT.md",
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_PROTOCOL_V1.md",
    "KRAKEN_AI_DRIVEN_V2_CONTEXT_SCORE_FORENSIC_REVIEW_ATTEMPT_1_RESULT.md",
    "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md",
    "src/kraken_ai_driven_v2_context_score_forensic_review.py",
    "src/kraken_ai_driven_v2_context_score_forensic_review_review.py",
    "src/kraken_ai_driven_v2_bidirectional_hypothesis.py",
)


def test_review_binds_forensic_closure_and_bidirectional_hypothesis():
    review = review_bidirectional_hypothesis(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"].startswith("bde314d")
    assert review["context_forensic_report_sha256"] == EXPECTED_CONTEXT_FORENSIC_REPORT_SHA256
    assert review["context_forensic_result_document_sha256"] == EXPECTED_CONTEXT_FORENSIC_RESULT_SHA256
    assert review["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert review["component_sha256"] == EXPECTED_COMPONENT_SHA256
    assert all(review["source_sha256_matches"].values())


def test_review_confirms_one_bounded_bidirectional_experiment():
    review = review_bidirectional_hypothesis(ROOT)

    assert review["long_only_derivatives_context_closed"] is True
    assert review["symmetric_long_short_labels_implemented"] is True
    assert review["same_bar_stop_first_implemented"] is True
    assert review["positive_maximum_action_rule_implemented"] is True
    assert review["new_indicator_count"] == 0
    assert review["spot_feature_count"] == 16
    assert review["context_feature_count"] == 9
    assert review["maximum_fold_model_fits"] == 12
    assert review["fold_plan_causal"] is True


def test_review_keeps_data_learning_and_execution_closed():
    review = review_bidirectional_hypothesis(ROOT)
    required_false = (
        "market_values_opened",
        "labels_generated",
        "model_training_executed",
        "feature_search_authorized",
        "hyperparameter_sweep_authorized",
        "threshold_sweep_authorized",
        "automatic_model_selection",
        "calibration_data_opened",
        "evaluation_data_opened",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "real_orders_submitted",
        "live_execution_authorized",
    )
    assert all(review[field] is False for field in required_false)


def test_review_rejects_any_bound_source_tamper(tmp_path):
    for relative in BOUND_FILES:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    component = tmp_path / "src" / "kraken_ai_driven_v2_bidirectional_hypothesis.py"
    component.write_bytes(component.read_bytes() + b"\n# tamper\n")

    with pytest.raises(RuntimeError, match="component"):
        review_bidirectional_hypothesis(tmp_path)

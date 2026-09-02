import os
from pathlib import Path
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_derivatives_context_hypothesis_review import (
    EXPECTED_COMPONENT_SHA256,
    EXPECTED_FEASIBILITY_REPORT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    STATUS,
    review_derivatives_context_hypothesis,
)


ROOT = Path(__file__).resolve().parents[1]


def test_review_binds_positive_audit_and_frozen_hypothesis():
    review = review_derivatives_context_hypothesis(ROOT)

    assert review["status"] == STATUS
    assert review["parent_commit"].startswith("99f6242")
    assert review["feasibility_report_sha256"] == EXPECTED_FEASIBILITY_REPORT_SHA256
    assert review["feasibility_protocol_sha256_match"] is True
    assert review["feasibility_component_sha256_match"] is True
    assert review["feasibility_review_sha256_match"] is True
    assert review["feasibility_result_document_sha256_match"] is True
    assert review["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert review["protocol_sha256_match"] is True
    assert review["component_sha256"] == EXPECTED_COMPONENT_SHA256
    assert review["component_sha256_match"] is True


def test_review_confirms_matched_causal_design_before_real_values():
    review = review_derivatives_context_hypothesis(ROOT)

    assert review["source_feasible"] is True
    assert review["causal_feature_schema_implemented"] is True
    assert review["matched_ablation_design_implemented"] is True
    assert review["fold_plan_causal"] is True
    assert review["context_feature_count"] == 9
    assert review["experiment_budget"] == 4
    assert review["maximum_fold_model_fits"] == 12
    assert len(review["matched_control"]) == 2
    assert review["control_variants_candidate_eligible"] is False


def test_review_keeps_all_real_learning_and_execution_boundaries_closed():
    review = review_derivatives_context_hypothesis(ROOT)
    required_false = (
        "market_values_opened",
        "labels_generated",
        "model_training_executed",
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


def test_review_fails_closed_if_protocol_or_component_changes(tmp_path):
    relatives = (
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_PROTOCOL_V1.md",
        "KRAKEN_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_FEASIBILITY_ATTEMPT_1_RESULT.md",
        "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_PROTOCOL_V1.md",
        "src/kraken_ai_driven_v2_derivatives_context_feasibility.py",
        "src/kraken_ai_driven_v2_derivatives_context_feasibility_review.py",
        "src/kraken_ai_driven_v2_derivatives_context_hypothesis.py",
    )
    for relative in relatives:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    component = tmp_path / "src" / "kraken_ai_driven_v2_derivatives_context_hypothesis.py"
    component.write_text(component.read_text(encoding="utf-8") + "\n# tamper\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="component"):
        review_derivatives_context_hypothesis(tmp_path)

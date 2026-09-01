from datetime import timedelta
import os
import sys

import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_12h_development_economic_review import (
    HOLD_CASH_STATUS,
    INTEREST_STATUS,
    economic_review_declaration,
    review_prediction_records,
    validate_prediction_records,
)
from kraken_ai_driven_v2_learning_core import ASSET_ORDER, FOLD_PLAN, MODEL_SPECS


def _iso(value):
    return value.isoformat().replace("+00:00", "Z")


def _records(*, eligible=True, overlap=False):
    records = []
    for fold in FOLD_PLAN:
        start = pd.Timestamp(fold["validation_start_utc"])
        training_end = fold["training_end_exclusive_utc"]
        for model_id in MODEL_SPECS:
            for asset in ASSET_ORDER:
                for index in range(12):
                    decision = start + timedelta(days=(2 if overlap else 20) * index)
                    event_end = decision + timedelta(days=10)
                    phase = index % 12
                    if phase < 6:
                        label, outcome = "TARGET_3R_FIRST", 3.0
                        target_probability = 0.60
                    elif phase < 11:
                        label, outcome = "STOP_1R_FIRST", -1.0
                        target_probability = 0.35
                    else:
                        label, outcome = "TIMEOUT_NO_BARRIER", 0.0
                        target_probability = 0.30
                    if eligible:
                        stop_probability = 0.30
                        timeout_probability = 1.0 - target_probability - stop_probability
                    else:
                        target_probability = 0.10
                        stop_probability = 0.80
                        timeout_probability = 0.10
                    records.append(
                        {
                            "fold_id": fold["fold_id"],
                            "model_id": model_id,
                            "asset": asset,
                            "decision_timestamp": _iso(decision),
                            "event_end_timestamp": _iso(event_end),
                            "training_end_timestamp": training_end,
                            "actual_label": label,
                            "actual_outcome_net_r": outcome,
                            "p_target_3r_first": target_probability,
                            "p_stop_1r_first": stop_probability,
                            "p_timeout_no_barrier": timeout_probability,
                        }
                    )
    return records


def test_declaration_is_inert_and_freezes_one_untuned_rule():
    declaration = economic_review_declaration()

    assert declaration["fixed_rule"] == "3*p_target_3r_first-p_stop_1r_first>0"
    assert declaration["threshold_sweep_authorized"] is False
    assert declaration["learning_evidence_opened"] is False
    assert declaration["model_artifacts_unpickled"] is False
    assert declaration["model_training_executed"] is False
    assert declaration["automatic_model_selection"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_stable_synthetic_oof_evidence_creates_review_interest_without_selection():
    result = review_prediction_records(_records())

    assert result["status"] == INTEREST_STATUS
    assert result["action"] == "REVIEW_DEVELOPMENT_ECONOMIC_INTEREST"
    assert result["model_families_with_interest"] == list(MODEL_SPECS)
    assert result["automatic_model_selection"] is False
    assert result["candidate_v2_authorized"] is False
    for model in result["model_reviews"]:
        assert model["development_economic_interest"] is True
        assert model["gates"]["all_folds_positive_net_r_pass"] is True
        assert model["gates"]["asset_breadth_pass"] is True
        assert model["gates"]["all_folds_positive_target_pr_auc_lift_pass"] is True


def test_negative_expected_reward_rule_returns_hold_cash():
    result = review_prediction_records(_records(eligible=False))

    assert result["status"] == HOLD_CASH_STATUS
    assert result["action"] == "HOLD_CASH"
    assert result["model_families_with_interest"] == []
    for model in result["model_reviews"]:
        assert model["raw_eligible_overall"]["count"] == 0
        assert model["nonoverlapping_eligible_overall"]["count"] == 0
        assert model["development_economic_interest"] is False


def test_nonoverlap_view_never_counts_concurrent_events_twice_per_asset():
    result = review_prediction_records(_records(overlap=True))

    for model in result["model_reviews"]:
        assert model["raw_eligible_overall"]["count"] == 108
        assert model["nonoverlapping_eligible_overall"]["count"] < 108
        for fold in model["folds"]:
            assert fold["raw_eligible"]["count"] == 36
            assert fold["nonoverlapping_eligible"]["count"] < 36


def test_validation_rejects_probability_and_duplicate_key_tampering():
    bad_probability = _records()
    bad_probability[0]["p_target_3r_first"] = 1.1
    with pytest.raises(RuntimeError, match="outside"):
        validate_prediction_records(bad_probability)

    duplicate = _records()
    duplicate.append(dict(duplicate[0]))
    with pytest.raises(RuntimeError, match="duplicated"):
        validate_prediction_records(duplicate)


def test_validation_rejects_noncausal_or_mismatched_model_event_sets():
    noncausal = _records()
    noncausal[0]["training_end_timestamp"] = noncausal[0]["event_end_timestamp"]
    with pytest.raises(RuntimeError, match="chronological"):
        validate_prediction_records(noncausal)

    mismatched = _records()
    mismatched[0]["actual_outcome_net_r"] = 2.5
    with pytest.raises(RuntimeError, match="same event set"):
        validate_prediction_records(mismatched)

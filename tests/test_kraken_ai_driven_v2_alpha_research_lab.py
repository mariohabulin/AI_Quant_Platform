import json
import math
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import kraken_ai_driven_v2_alpha_research_lab as lab_module
from kraken_ai_driven_v2_alpha_research_lab import (
    INNER_FIT_FRACTION,
    MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
    MINIMUM_RAW_SELECTIONS_PER_FOLD,
    PROTOCOL_ID,
    RESULT_STATUS_HOLD,
    RESULT_STATUS_PASS,
    VARIANT_SPECS,
    _nonoverlapping,
    _outer_and_inner_slices,
    _variant_review,
    alpha_research_lab_declaration,
    canonical_json_bytes,
    run_alpha_research_lab,
)
from kraken_ai_driven_v2_learning_core import (
    ASSET_ORDER,
    CLASS_ORDER,
    FEATURE_COLUMNS,
    FOLD_PLAN,
)


def _learning_table():
    dates = pd.date_range(
        "2019-04-01T00:00:00Z",
        "2024-03-01T00:00:00Z",
        freq="2D",
        tz="UTC",
    )
    rows = []
    outcome = {CLASS_ORDER[0]: 3.0, CLASS_ORDER[1]: -1.0, CLASS_ORDER[2]: 0.0}
    for asset_number, asset in enumerate(ASSET_ORDER):
        for number, timestamp in enumerate(dates):
            label = CLASS_ORDER[number % len(CLASS_ORDER)]
            signal = math.sin(number / 5.0 + asset_number)
            row = {
                "asset": asset,
                "decision_timestamp": timestamp,
                "event_end_timestamp": timestamp + pd.Timedelta(days=1),
                "label": label,
                "outcome_net_r": outcome[label],
            }
            for feature_number, feature in enumerate(FEATURE_COLUMNS):
                row[feature] = signal + 0.01 * feature_number + 0.05 * asset_number
            rows.append(row)
    return pd.DataFrame(rows)


def _predictions(*, profitable):
    rows = []
    for fold_number, fold in enumerate(FOLD_PLAN):
        start = pd.Timestamp(fold["validation_start_utc"])
        for number in range(36):
            timestamp = start + pd.Timedelta(days=2 * number)
            asset = ASSET_ORDER[number % len(ASSET_ORDER)]
            positive = profitable or fold_number < 2
            rows.append(
                {
                    "fold_id": fold["fold_id"],
                    "asset": asset,
                    "decision_timestamp": timestamp,
                    "event_end_timestamp": timestamp + pd.Timedelta(hours=12),
                    "label": CLASS_ORDER[0] if positive else CLASS_ORDER[1],
                    "outcome_net_r": 3.0 if positive else -1.0,
                    "score": 0.5,
                    "eligible": True,
                }
            )
    return pd.DataFrame(rows)


def _fold_metadata():
    return {
        fold["fold_id"]: {
            "fold_id": fold["fold_id"],
            "inner_boundary_utc": pd.Timestamp(fold["validation_start_utc"])
            - pd.Timedelta(days=30),
            "inner_fit_rows": 300,
            "inner_calibration_rows": 100,
            "outer_validation_rows": 108,
            "inner_fit_class_counts": {label: 100 for label in CLASS_ORDER},
            "inner_calibration_class_counts": {label: 33 for label in CLASS_ORDER},
            "outer_validation_class_counts": {label: 36 for label in CLASS_ORDER},
            "predictive_metrics": {},
        }
        for fold in FOLD_PLAN
    }


def test_declaration_freezes_one_six_variant_development_lab():
    declaration = alpha_research_lab_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["active_resolution"] == "12h"
    assert declaration["partition"] == "DEVELOPMENT"
    assert declaration["experiment_budget"] == 6
    assert declaration["variant_order"] == list(VARIANT_SPECS)
    assert declaration["inner_fit_fraction"] == INNER_FIT_FRACTION == 0.75
    assert declaration["hyperparameter_sweep_authorized"] is False
    assert declaration["threshold_sweep_authorized"] is False
    assert declaration["automatic_candidate_promotion"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False


def test_registry_has_three_classifiers_and_three_direct_net_r_regressors():
    objectives = [spec["objective"] for spec in VARIANT_SPECS.values()]

    assert len(VARIANT_SPECS) == 6
    assert objectives.count("CALIBRATED_THREE_CLASS_UTILITY") == 3
    assert objectives.count("DIRECT_EXPECTED_NET_R") == 3
    assert VARIANT_SPECS["NATURAL_LOGISTIC_CLASSIFIER"]["parameters"]["class_weight"] is None
    assert VARIANT_SPECS["EXTRA_TREES_CLASSIFIER"]["parameters"]["class_weight"] is None


def test_nested_split_is_chronological_and_purged():
    table = _learning_table()

    for fold in FOLD_PLAN:
        inner_fit, inner_calibration, validation, boundary = _outer_and_inner_slices(
            table, fold
        )
        training_end = pd.Timestamp(fold["training_end_exclusive_utc"])
        validation_start = pd.Timestamp(fold["validation_start_utc"])
        assert inner_fit["decision_timestamp"].max() < boundary
        assert inner_fit["event_end_timestamp"].max() < boundary
        assert inner_calibration["decision_timestamp"].min() >= boundary
        assert inner_calibration["event_end_timestamp"].max() < training_end
        assert validation["decision_timestamp"].min() >= validation_start
        assert set(inner_fit["label"]) == set(CLASS_ORDER)
        assert set(inner_calibration["label"]) == set(CLASS_ORDER)


def test_nonoverlapping_view_allows_only_one_live_event_per_asset():
    timestamp = pd.Timestamp("2022-01-01T00:00:00Z")
    frame = pd.DataFrame(
        [
            {
                "asset": "BTC-USD",
                "decision_timestamp": timestamp + pd.Timedelta(hours=offset),
                "event_end_timestamp": timestamp + pd.Timedelta(hours=offset + 24),
                "label": CLASS_ORDER[0],
                "outcome_net_r": 3.0,
            }
            for offset in (0, 12, 24, 36)
        ]
    )

    selected = _nonoverlapping(frame)

    assert list(selected["decision_timestamp"]) == [
        timestamp,
        timestamp + pd.Timedelta(hours=24),
    ]


def test_economic_gates_accept_persistent_profit_and_reject_one_negative_fold():
    passing = _variant_review(
        "RIDGE_NET_R_REGRESSOR", _predictions(profitable=True), _fold_metadata()
    )
    failing = _variant_review(
        "RIDGE_NET_R_REGRESSOR", _predictions(profitable=False), _fold_metadata()
    )

    assert passing["development_viable"] is True
    assert passing["gates"]["all_fold_raw_support_pass"] is True
    assert passing["gates"]["all_fold_nonoverlap_support_pass"] is True
    assert passing["raw_eligible_overall"]["count"] >= (
        len(FOLD_PLAN) * MINIMUM_RAW_SELECTIONS_PER_FOLD
    )
    assert all(
        fold["nonoverlapping_eligible"]["count"]
        >= MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD
        for fold in passing["folds"]
    )
    assert failing["development_viable"] is False
    assert failing["gates"]["all_fold_positive_net_r_pass"] is False


def test_real_nested_lab_executes_all_six_and_never_promotes_candidate():
    result = run_alpha_research_lab(_learning_table())

    assert result["status"] in {RESULT_STATUS_PASS, RESULT_STATUS_HOLD}
    assert result["executed_variant_count"] == 6
    assert [review["variant_id"] for review in result["variant_reviews"]] == list(
        VARIANT_SPECS
    )
    assert result["automatic_candidate_promotion"] is False
    assert result["candidate_v2_authorized"] is False
    assert result["calibration_data_opened"] is False
    assert result["evaluation_data_opened"] is False
    assert len(canonical_json_bytes(result)) > 1000


def test_no_viable_variant_returns_hold_cash(monkeypatch):
    def always_negative(variant_id, inner_fit, inner_calibration, validation):
        prediction = validation[
            ["asset", "decision_timestamp", "event_end_timestamp", "label", "outcome_net_r"]
        ].copy()
        prediction["score"] = -1.0
        prediction["eligible"] = False
        return prediction, {"mean_predicted_net_r": -1.0}

    monkeypatch.setattr(lab_module, "_fit_predict_variant", always_negative)
    result = run_alpha_research_lab(_learning_table())

    assert result["status"] == RESULT_STATUS_HOLD
    assert result["action"] == "HOLD_CASH"
    assert result["selected_development_variant"] is None
    assert result["executed_variant_count"] == 6
    assert result["next_stage"] == "CLOSE_12H_OHLCV_HYPOTHESIS_HOLD_CASH"


def test_canonical_json_rejects_nonfinite_results():
    with pytest.raises(ValueError, match="non-finite"):
        canonical_json_bytes({"invalid": np.nan})


def test_protocol_records_the_frozen_stop_conditions():
    protocol = (
        Path(__file__).resolve().parents[1]
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_ALPHA_RESEARCH_LAB_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")

    for marker in (
        "exactly six",
        "no seventh variant",
        "Calibration and Evaluation access: prohibited",
        "HOLD_CASH",
        "automatic Candidate promotion: prohibited",
    ):
        assert marker in protocol


def test_output_contract_contains_only_finite_json_values():
    payload = canonical_json_bytes(alpha_research_lab_declaration())
    parsed = json.loads(payload)

    assert parsed["experiment_budget"] == 6
    assert b"NaN" not in payload

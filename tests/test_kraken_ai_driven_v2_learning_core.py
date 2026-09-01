import hashlib
import math
import os
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_learning_core import (
    ACTIVE_RESOLUTION,
    ASSET_ORDER,
    CLASS_ORDER,
    DEVELOPMENT_END_EXCLUSIVE_UTC,
    FEATURE_COLUMNS,
    MODEL_SPECS,
    ZERO_COST_PROFILE,
    build_causal_feature_table,
    build_labeled_learning_data,
    build_labeled_learning_table,
    learning_core_declaration,
    train_walk_forward,
    triple_barrier_label,
    validate_development_frames,
)


def _market_frame(start="2019-01-01T00:00:00Z", periods=500, phase=0.0):
    index = pd.date_range(start, periods=periods, freq="12h", tz="UTC")
    x = np.arange(periods, dtype=float)
    close = 100.0 + 0.018 * x + 4.0 * np.sin(x / 13.0 + phase)
    open_ = close * (1.0 + 0.001 * np.sin(x / 5.0 + phase))
    high = np.maximum(open_, close) + 1.0 + 0.2 * np.sin(x / 7.0) ** 2
    low = np.minimum(open_, close) - 1.0 - 0.2 * np.cos(x / 7.0) ** 2
    volume = 1000.0 + 100.0 * np.cos(x / 11.0 + phase) + x
    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def _frames(periods=500):
    return {
        asset: _market_frame(periods=periods, phase=offset)
        for asset, offset in zip(ASSET_ORDER, (0.0, 0.7, 1.4), strict=True)
    }


def _barrier_frame(highs, lows, opens=None):
    periods = len(highs)
    index = pd.date_range("2020-01-01", periods=periods, freq="12h", tz="UTC")
    opens = [100.0] * periods if opens is None else opens
    closes = [100.0] * periods
    return pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": [1000.0] * periods,
        },
        index=index,
    )


def _learning_table():
    dates = pd.date_range(
        "2019-04-01T00:00:00Z",
        "2024-03-01T00:00:00Z",
        freq="2D",
        tz="UTC",
    )
    rows = []
    for asset_number, asset in enumerate(ASSET_ORDER):
        for number, timestamp in enumerate(dates):
            signal = math.sin(number / 5.0 + asset_number)
            label = CLASS_ORDER[number % len(CLASS_ORDER)]
            row = {
                "asset": asset,
                "decision_timestamp": timestamp,
                "event_end_timestamp": timestamp + pd.Timedelta(days=1),
                "label": label,
                "outcome_net_r": {CLASS_ORDER[0]: 3.0, CLASS_ORDER[1]: -1.0, CLASS_ORDER[2]: 0.0}[label],
            }
            for feature_number, feature in enumerate(FEATURE_COLUMNS):
                row[feature] = signal + 0.01 * feature_number + 0.05 * asset_number
            rows.append(row)
    return pd.DataFrame(rows)


def test_declaration_is_an_executable_learning_core_not_another_strategy_round():
    declaration = learning_core_declaration()

    assert declaration["status"] == "KRAKEN_AI_V2_LEARNING_CORE_IMPLEMENTED_REAL_DEVELOPMENT_RUN_REQUIRED"
    assert declaration["active_resolution"] == ACTIVE_RESOLUTION == "12h"
    assert declaration["rule_discovery_rounds_active"] is False
    assert declaration["causal_features_implemented"] is True
    assert declaration["triple_barrier_labels_implemented"] is True
    assert declaration["walk_forward_training_implemented"] is True
    assert declaration["parameters_learned_from_labels"] is True
    assert declaration["real_development_training_executed"] is False
    assert declaration["calibration_data_opened"] is False
    assert declaration["evaluation_data_opened"] is False
    assert declaration["candidate_v2_authorized"] is False


def test_model_budget_is_two_real_learners_without_an_automatic_winner():
    assert tuple(MODEL_SPECS) == ("LOGISTIC_BASELINE", "HIST_GBT_CHALLENGER")
    assert MODEL_SPECS["LOGISTIC_BASELINE"]["family"] == "MULTINOMIAL_LOGISTIC_REGRESSION"
    assert MODEL_SPECS["HIST_GBT_CHALLENGER"]["family"] == "HISTOGRAM_GRADIENT_BOOSTING"
    assert all(spec["learns_parameters"] for spec in MODEL_SPECS.values())
    assert all(not spec["automatic_promotion"] for spec in MODEL_SPECS.values())


def test_frame_validation_is_strictly_development_only_and_twelve_hour():
    frames = _frames(220)
    validated = validate_development_frames(frames)
    assert tuple(validated) == ASSET_ORDER

    wrong_frequency = _frames(220)
    wrong = wrong_frequency["BTC-USD"].copy()
    changed_index = list(wrong.index)
    changed_index[50] = changed_index[50] + pd.Timedelta(hours=1)
    wrong.index = pd.DatetimeIndex(changed_index)
    wrong_frequency["BTC-USD"] = wrong
    with pytest.raises(ValueError, match="continuous 12h grid"):
        validate_development_frames(wrong_frequency)

    future = _frames(220)
    shifted = future["ETH-USD"].copy()
    shifted.index = shifted.index + pd.DateOffset(years=6)
    future["ETH-USD"] = shifted
    with pytest.raises(ValueError, match="Development boundary"):
        validate_development_frames(future)


def test_causal_features_have_a_frozen_schema_and_no_future_dependency():
    frames = _frames(420)
    original = build_causal_feature_table(frames)

    changed = {asset: frame.copy() for asset, frame in frames.items()}
    cutoff = changed["BTC-USD"].index[320]
    for frame in changed.values():
        frame.loc[frame.index > cutoff, ["Open", "High", "Low", "Close"]] *= 7.0
        frame.loc[frame.index > cutoff, "Volume"] *= 11.0
    modified = build_causal_feature_table(changed)

    assert set(FEATURE_COLUMNS).issubset(original.columns)
    left = original.loc[original["decision_timestamp"] <= cutoff].reset_index(drop=True)
    right = modified.loc[modified["decision_timestamp"] <= cutoff].reset_index(drop=True)
    pd.testing.assert_frame_equal(left, right)
    assert np.isfinite(original[list(FEATURE_COLUMNS)].to_numpy()).all()


@pytest.mark.parametrize(
    ("highs", "lows", "expected"),
    [
        ([101, 110, 101, 101], [99, 99, 99, 99], "TARGET_3R_FIRST"),
        ([101, 101, 101, 101], [99, 96, 99, 99], "STOP_1R_FIRST"),
        ([101, 110, 101, 101], [99, 96, 99, 99], "STOP_1R_FIRST"),
        ([101, 101, 101, 101], [99, 99, 99, 99], "TIMEOUT_NO_BARRIER"),
    ],
)
def test_triple_barrier_label_uses_next_open_and_stop_first(highs, lows, expected):
    frame = _barrier_frame(highs, lows)
    outcome = triple_barrier_label(
        frame,
        decision_position=0,
        signal_atr=2.0,
        horizon_bars=3,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert outcome.valid is True
    assert outcome.label == expected
    assert outcome.entry_timestamp == frame.index[1]
    assert outcome.stop_trigger_price == pytest.approx(97.0)
    assert outcome.target_trigger_price == pytest.approx(109.0)


def test_labeler_rejects_provider_gaps_and_right_censoring():
    frame = _barrier_frame([101] * 5, [99] * 5)
    gapped = frame.drop(frame.index[2])

    gap = triple_barrier_label(
        gapped,
        decision_position=0,
        signal_atr=2.0,
        horizon_bars=3,
        cost_profile=ZERO_COST_PROFILE,
    )
    censored = triple_barrier_label(
        frame,
        decision_position=3,
        signal_atr=2.0,
        horizon_bars=3,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert gap.valid is False
    assert gap.invalid_reason == "PROVIDER_GAP_CENSORED"
    assert censored.valid is False
    assert censored.invalid_reason == "RIGHT_EDGE_CENSORED"


def test_learning_table_contains_features_and_outcomes_but_no_future_raw_columns():
    table = build_labeled_learning_table(_frames(500))

    assert len(table) > 0
    assert set(table["asset"]) == set(ASSET_ORDER)
    assert set(table["label"]).issubset(set(CLASS_ORDER))
    assert set(FEATURE_COLUMNS).issubset(table.columns)
    assert "future_high" not in table
    assert "future_low" not in table
    assert (table["event_end_timestamp"] > table["decision_timestamp"]).all()


def test_labeled_learning_data_reports_censoring_and_class_counts():
    result = build_labeled_learning_data(_frames(500))

    assert result.table.equals(build_labeled_learning_table(_frames(500)))
    for asset in ASSET_ORDER:
        observed = result.table.loc[result.table["asset"] == asset, "label"].value_counts()
        diagnostics = result.diagnostics[asset]
        assert diagnostics["labeled_rows"] == int(observed.sum())
        assert diagnostics["feature_rows"] >= diagnostics["labeled_rows"]
        assert diagnostics["label_counts"] == {
            label: int(observed.get(label, 0)) for label in CLASS_ORDER
        }
        assert sum(diagnostics["invalid_reason_counts"].values()) == (
            diagnostics["feature_rows"] - diagnostics["labeled_rows"]
        )


def test_walk_forward_fits_real_parameters_and_only_predicts_unseen_rows():
    result = train_walk_forward(
        _learning_table(),
        model_ids=("LOGISTIC_BASELINE",),
        minimum_training_class_count=20,
        minimum_validation_class_count=10,
    )

    assert result.parameters_learned_from_labels is True
    assert result.automatic_model_selected is False
    assert result.trained_model_count == 3
    assert set(result.predictions["fold_id"]) == {"FOLD_1", "FOLD_2", "FOLD_3"}
    assert set(result.predictions["model_id"]) == {"LOGISTIC_BASELINE"}
    probabilities = result.predictions[
        ["p_target_3r_first", "p_stop_1r_first", "p_timeout_no_barrier"]
    ]
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0)
    assert (result.predictions["decision_timestamp"] > result.predictions["training_end_timestamp"]).all()
    assert len(result.model_artifact_sha256) == result.trained_model_count
    assert all(len(value) == 64 for value in result.model_artifact_sha256.values())
    assert set(result.model_artifact_bytes) == set(result.model_artifact_sha256)
    assert {
        key: hashlib.sha256(value).hexdigest()
        for key, value in result.model_artifact_bytes.items()
    } == result.model_artifact_sha256


def test_walk_forward_is_deterministic_and_reports_predictive_metrics():
    table = _learning_table()
    first = train_walk_forward(
        table,
        model_ids=("LOGISTIC_BASELINE",),
        minimum_training_class_count=20,
        minimum_validation_class_count=10,
    )
    second = train_walk_forward(
        table,
        model_ids=("LOGISTIC_BASELINE",),
        minimum_training_class_count=20,
        minimum_validation_class_count=10,
    )

    pd.testing.assert_frame_equal(first.predictions, second.predictions)
    assert first.model_artifact_sha256 == second.model_artifact_sha256
    assert first.model_artifact_bytes == second.model_artifact_bytes
    assert set(first.metrics) == {
        "FOLD_1|LOGISTIC_BASELINE",
        "FOLD_2|LOGISTIC_BASELINE",
        "FOLD_3|LOGISTIC_BASELINE",
    }
    for metric in first.metrics.values():
        assert metric["validation_rows"] > 0
        assert math.isfinite(metric["multiclass_log_loss"])
        assert math.isfinite(metric["target_brier_score"])
        assert metric["training_class_counts"].keys() == metric["validation_class_counts"].keys()


def test_both_registered_model_families_fit_without_automatic_selection():
    result = train_walk_forward(
        _learning_table(),
        minimum_training_class_count=20,
        minimum_validation_class_count=10,
    )

    assert result.trained_model_count == 6
    assert set(result.predictions["model_id"]) == set(MODEL_SPECS)
    assert result.automatic_model_selected is False
    assert len(result.model_artifact_sha256) == 6


def test_training_fails_closed_when_a_fold_lacks_class_support():
    table = _learning_table()
    table.loc[table["decision_timestamp"] < pd.Timestamp("2021-03-02", tz="UTC"), "label"] = CLASS_ORDER[0]

    with pytest.raises(ValueError, match="class support"):
        train_walk_forward(
            table,
            model_ids=("LOGISTIC_BASELINE",),
            minimum_training_class_count=2,
            minimum_validation_class_count=2,
        )


def test_calibration_and_evaluation_rows_are_rejected_before_training():
    table = _learning_table()
    forbidden = table.iloc[[0]].copy()
    forbidden["decision_timestamp"] = pd.Timestamp(DEVELOPMENT_END_EXCLUSIVE_UTC)
    forbidden["event_end_timestamp"] = pd.Timestamp(DEVELOPMENT_END_EXCLUSIVE_UTC) + pd.Timedelta(days=1)
    table = pd.concat([table, forbidden], ignore_index=True)

    with pytest.raises(ValueError, match="Development partition"):
        train_walk_forward(table, model_ids=("LOGISTIC_BASELINE",))

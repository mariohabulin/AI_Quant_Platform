import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_derivatives_context_hypothesis import (
    ASSET_ORDER,
    BAR_INTERVAL,
    COMMON_END_EXCLUSIVE_UTC,
    COMMON_START_UTC,
    CONTEXT_FEATURE_COLUMNS,
    CONTEXT_WARMUP_BARS,
    EMPTY_CONTROL_SELECTION_BENCHMARK_NET_R,
    FEASIBILITY_REPORT_SHA256,
    FOLD_PLAN,
    MATCHED_CONTROL,
    MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD,
    MINIMUM_POSITIVE_ASSETS,
    MINIMUM_PREDICTIVE_FOLD_WINS,
    MINIMUM_RAW_SELECTIONS_PER_FOLD,
    PROTOCOL_ID,
    SPOT_FEATURE_COLUMNS,
    VARIANT_SPECS,
    build_asset_derivatives_context_features,
    build_derivatives_context_feature_table,
    derivatives_context_hypothesis_declaration,
    fold_plan_is_causal,
)


ROOT = Path(__file__).resolve().parents[1]


def _source_frames(periods=180, start="2022-01-01T00:00:00Z", asset_shift=0.0):
    decisions = pd.date_range(start, periods=periods, freq="12h", tz="UTC")
    effective = decisions + BAR_INTERVAL
    funding_index = pd.date_range(
        decisions[0], effective[-1], freq="8h", tz="UTC"
    )
    funding = pd.DataFrame(
        {"funding_rate": 0.0001 + np.sin(np.arange(len(funding_index)) / 9.0) * 0.00002},
        index=funding_index,
    )
    oi_index = pd.date_range(
        decisions[0], effective[-1], freq="30min", tz="UTC"
    )
    open_interest = pd.DataFrame(
        {
            "open_interest": 10000.0
            + asset_shift
            + np.arange(len(oi_index), dtype=float) * 0.5
        },
        index=oi_index,
    )
    phase = np.arange(len(decisions), dtype=float)
    index_close = 100.0 + asset_shift + phase * 0.03
    basis = 0.001 + np.sin(phase / 13.0) * 0.0004
    mark_index = pd.DataFrame(
        {
            "mark_close": index_close * (1.0 + basis),
            "index_close": index_close,
        },
        index=decisions,
    )
    return decisions, funding, open_interest, mark_index


def test_declaration_freezes_one_matched_new_information_experiment():
    declaration = derivatives_context_hypothesis_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"].startswith("99f6242")
    assert declaration["feasibility_report_sha256"] == FEASIBILITY_REPORT_SHA256
    assert declaration["source_feasible"] is True
    assert declaration["common_start_utc"] == COMMON_START_UTC
    assert declaration["common_end_exclusive_utc"] == COMMON_END_EXCLUSIVE_UTC
    assert declaration["spot_feature_count"] == len(SPOT_FEATURE_COLUMNS) == 16
    assert declaration["context_feature_count"] == len(CONTEXT_FEATURE_COLUMNS) == 9
    assert declaration["experiment_budget"] == 4
    assert declaration["maximum_fold_model_fits"] == 12
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert EMPTY_CONTROL_SELECTION_BENCHMARK_NET_R == 0.0
    assert declaration["empty_control_selection_benchmark_net_r"] == 0.0


def test_variant_registry_is_two_exact_matched_ablation_pairs():
    assert list(VARIANT_SPECS) == [
        "SPOT_ONLY_HIST_GBT_CLASSIFIER_CONTROL",
        "SPOT_CONTEXT_HIST_GBT_CLASSIFIER",
        "SPOT_ONLY_HIST_GBT_NET_R_CONTROL",
        "SPOT_CONTEXT_HIST_GBT_NET_R",
    ]
    for context_id, control_id in MATCHED_CONTROL.items():
        context = VARIANT_SPECS[context_id]
        control = VARIANT_SPECS[control_id]
        assert context["objective"] == control["objective"]
        assert context["model_family"] == control["model_family"]
        assert context["parameters"] == control["parameters"]
        assert context["candidate_eligible"] is True
        assert control["candidate_eligible"] is False


def test_fold_plan_has_three_expanding_purged_unseen_windows():
    assert fold_plan_is_causal() is True
    assert len(FOLD_PLAN) == 3
    assert FOLD_PLAN[-1]["validation_end_exclusive_utc"] == COMMON_END_EXCLUSIVE_UTC
    for fold in FOLD_PLAN:
        training_end = pd.Timestamp(fold["training_end_exclusive_utc"])
        validation_start = pd.Timestamp(fold["validation_start_utc"])
        assert validation_start - training_end == pd.Timedelta(days=30)


def test_feature_engine_returns_exact_finite_schema_after_frozen_warmup():
    decisions, funding, open_interest, mark_index = _source_frames()

    features = build_asset_derivatives_context_features(
        funding, open_interest, mark_index, decisions
    )

    assert tuple(features.columns) == CONTEXT_FEATURE_COLUMNS
    assert features.index.min() == decisions[CONTEXT_WARMUP_BARS - 1]
    assert len(features) == len(decisions) - CONTEXT_WARMUP_BARS + 1
    assert np.isfinite(features.to_numpy(dtype=float)).all()


def test_basis_and_open_interest_formulas_are_frozen():
    decisions, funding, open_interest, mark_index = _source_frames()
    features = build_asset_derivatives_context_features(
        funding, open_interest, mark_index, decisions
    )
    timestamp = features.index[-1]
    expected_basis = (
        mark_index.loc[timestamp, "mark_close"]
        / mark_index.loc[timestamp, "index_close"]
        - 1.0
    )
    assert features.loc[timestamp, "basis_fraction"] == pytest.approx(expected_basis)
    assert features.loc[timestamp, "open_interest_log_change_1"] > 0.0
    assert features.loc[timestamp, "open_interest_log_change_6"] > 0.0


def test_future_source_changes_cannot_change_earlier_features():
    decisions, funding, open_interest, mark_index = _source_frames(periods=200)
    original = build_asset_derivatives_context_features(
        funding, open_interest, mark_index, decisions
    )
    cutoff = decisions[139]

    changed_funding = funding.copy()
    changed_oi = open_interest.copy()
    changed_mark = mark_index.copy()
    changed_funding.loc[changed_funding.index > cutoff + BAR_INTERVAL, "funding_rate"] *= 100.0
    changed_oi.loc[changed_oi.index > cutoff + BAR_INTERVAL, "open_interest"] *= 10.0
    changed_mark.loc[changed_mark.index > cutoff, "mark_close"] *= 2.0

    changed = build_asset_derivatives_context_features(
        changed_funding, changed_oi, changed_mark, decisions
    )
    pd.testing.assert_frame_equal(original.loc[:cutoff], changed.loc[:cutoff])


def test_stale_open_interest_invalidates_rows_and_rolling_context():
    decisions, funding, open_interest, mark_index = _source_frames(periods=180)
    gap_start = decisions[80] + BAR_INTERVAL
    gap_end = decisions[85] + BAR_INTERVAL
    incomplete_oi = open_interest.loc[
        (open_interest.index < gap_start) | (open_interest.index > gap_end)
    ]

    features = build_asset_derivatives_context_features(
        funding, incomplete_oi, mark_index, decisions
    )

    assert decisions[80] in features.index
    assert not any(timestamp in features.index for timestamp in decisions[81:145])
    assert features.index.max() == decisions[-1]


def test_constant_complete_context_has_defined_zero_zscores():
    decisions, funding, open_interest, mark_index = _source_frames(periods=100)
    funding["funding_rate"] = 0.0001
    open_interest["open_interest"] = 10000.0
    mark_index["mark_close"] = mark_index["index_close"] * 1.001

    features = build_asset_derivatives_context_features(
        funding, open_interest, mark_index, decisions
    )

    assert (features["funding_rate_zscore_60"] == 0.0).all()
    assert (features["open_interest_log_zscore_60"] == 0.0).all()
    assert (features["basis_zscore_60"] == 0.0).all()


def test_multi_asset_table_uses_exact_registry_and_stable_order():
    sources = {}
    decisions_by_asset = {}
    for number, asset in enumerate(ASSET_ORDER):
        decisions, funding, open_interest, mark_index = _source_frames(
            asset_shift=number * 10.0
        )
        decisions_by_asset[asset] = decisions
        sources[asset] = {
            "funding": funding,
            "open_interest": open_interest,
            "mark_index_12h": mark_index,
        }

    table = build_derivatives_context_feature_table(sources, decisions_by_asset)

    assert set(table["asset"]) == set(ASSET_ORDER)
    assert list(table.columns) == [*CONTEXT_FEATURE_COLUMNS, "asset", "decision_timestamp"]
    assert table.equals(
        table.sort_values(["decision_timestamp", "asset"], kind="stable").reset_index(
            drop=True
        )
    )


@pytest.mark.parametrize(
    "mutation,match",
    [
        ("naive_decisions", "timezone-aware"),
        ("future_decisions", "common Development interval"),
        ("bad_funding_columns", "columns must be exactly"),
        ("nonpositive_oi", "must be positive"),
        ("nonpositive_index", "must be positive"),
    ],
)
def test_input_contract_fails_closed(mutation, match):
    decisions, funding, open_interest, mark_index = _source_frames()
    if mutation == "naive_decisions":
        decisions = decisions.tz_localize(None)
    elif mutation == "future_decisions":
        decisions = pd.date_range("2024-04-01", periods=180, freq="12h", tz="UTC")
        mark_index.index = decisions
    elif mutation == "bad_funding_columns":
        funding = funding.rename(columns={"funding_rate": "value"})
    elif mutation == "nonpositive_oi":
        open_interest.iloc[0, 0] = 0.0
    elif mutation == "nonpositive_index":
        mark_index.iloc[0, 1] = 0.0
    with pytest.raises((TypeError, ValueError), match=match):
        build_asset_derivatives_context_features(
            funding, open_interest, mark_index, decisions
        )


def test_declaration_keeps_values_learning_and_later_partitions_closed():
    declaration = derivatives_context_hypothesis_declaration()
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
    assert all(declaration[field] is False for field in required_false)
    assert declaration["control_variants_candidate_eligible"] is False
    assert declaration["minimum_raw_selections_per_fold"] == MINIMUM_RAW_SELECTIONS_PER_FOLD
    assert (
        declaration["minimum_nonoverlapping_selections_per_fold"]
        == MINIMUM_NONOVERLAPPING_SELECTIONS_PER_FOLD
    )
    assert declaration["minimum_positive_assets"] == MINIMUM_POSITIVE_ASSETS
    assert declaration["minimum_predictive_fold_wins"] == MINIMUM_PREDICTIVE_FOLD_WINS


def test_protocol_states_incremental_attribution_and_no_hidden_retry():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_DERIVATIVES_CONTEXT_LEARNING_HYPOTHESIS_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    assert "incremental information" in protocol
    assert "Control and context variants use the same context-complete rows" in protocol
    assert "Exactly nine new features" in protocol
    assert "higher overall and worst-fold mean net R" in protocol
    assert "frozen economic comparator of `0.0 R`" in protocol
    assert "There is no learner, hyperparameter or threshold sweep" in protocol
    assert "Calibration and Evaluation: unopened" in protocol

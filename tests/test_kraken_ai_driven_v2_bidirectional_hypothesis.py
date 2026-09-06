import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_bidirectional_hypothesis import (
    ACTION_ORDER,
    ALL_NUMERIC_FEATURE_COLUMNS,
    CONTEXT_FEATURE_COLUMNS,
    CONTEXT_FORENSIC_REPORT_SHA256,
    DIRECTION_ORDER,
    FOLD_PLAN,
    HORIZON_BARS,
    LONG_ONLY_CLOSURE_STATUS,
    MATCHED_CONTROL,
    PARENT_COMMIT,
    PROTOCOL_ID,
    SPOT_FEATURE_COLUMNS,
    VARIANT_SPECS,
    bidirectional_hypothesis_declaration,
    build_directional_outcome_pair,
    directional_triple_barrier_label,
    select_bidirectional_action,
)
from kraken_ai_driven_v2_learning_core import ZERO_COST_PROFILE, triple_barrier_label


ROOT = Path(__file__).resolve().parents[1]


def _frame(prices, *, start="2022-01-01T00:00:00Z"):
    values = np.asarray(prices, dtype=float)
    return pd.DataFrame(
        {
            "Open": values,
            "High": values + 0.1,
            "Low": values - 0.1,
            "Close": values,
            "Volume": np.full(len(values), 1000.0),
        },
        index=pd.date_range(start, periods=len(values), freq="12h", tz="UTC"),
    )


def test_declaration_freezes_only_the_bidirectional_material_change():
    declaration = bidirectional_hypothesis_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["parent_commit"].startswith("bde314d")
    assert declaration["context_forensic_report_sha256"] == CONTEXT_FORENSIC_REPORT_SHA256
    assert declaration["long_only_closure_status"] == LONG_ONLY_CLOSURE_STATUS
    assert declaration["direction_order"] == list(DIRECTION_ORDER) == ["LONG", "SHORT"]
    assert declaration["action_order"] == list(ACTION_ORDER)
    assert declaration["new_indicator_count"] == 0
    assert declaration["horizon_bars"] == HORIZON_BARS == 60
    assert declaration["horizon_days"] == 30
    assert declaration["risk_atr_multiplier"] == 1.5
    assert declaration["target_r"] == 3.0
    assert declaration["stop_r"] == 1.0


def test_feature_registry_reuses_exact_16_plus_9_schema():
    declaration = bidirectional_hypothesis_declaration()

    assert len(SPOT_FEATURE_COLUMNS) == declaration["spot_feature_count"] == 16
    assert len(CONTEXT_FEATURE_COLUMNS) == declaration["context_feature_count"] == 9
    assert tuple(ALL_NUMERIC_FEATURE_COLUMNS) == (
        *SPOT_FEATURE_COLUMNS,
        *CONTEXT_FEATURE_COLUMNS,
    )
    assert len(ALL_NUMERIC_FEATURE_COLUMNS) == declaration["maximum_numeric_feature_count"] == 25


def test_variant_budget_is_two_feature_sets_times_two_directions_times_three_folds():
    declaration = bidirectional_hypothesis_declaration()

    assert list(VARIANT_SPECS) == [
        "SPOT_ONLY_BIDIRECTIONAL_HIST_GBT_NET_R_CONTROL",
        "SPOT_CONTEXT_BIDIRECTIONAL_HIST_GBT_NET_R",
    ]
    assert declaration["matched_control"] == MATCHED_CONTROL
    assert declaration["directional_model_count_per_fold"] == 4
    assert declaration["maximum_fold_model_fits"] == 12
    assert len(FOLD_PLAN) == 3
    for spec in VARIANT_SPECS.values():
        assert spec["objective"] == "BIDIRECTIONAL_DIRECT_EXPECTED_NET_R"
        assert spec["model_family"] == "HISTOGRAM_GRADIENT_BOOSTING_REGRESSOR"
        assert spec["absolute_gate_eligible"] is True


def test_long_label_is_exactly_the_existing_frozen_label():
    frame = _frame([100.0] * 70)
    legacy = triple_barrier_label(
        frame,
        decision_position=0,
        signal_atr=2.0,
        horizon_bars=60,
        cost_profile=ZERO_COST_PROFILE,
    )
    directional = directional_triple_barrier_label(
        frame,
        direction="LONG",
        decision_position=0,
        signal_atr=2.0,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert directional.valid is True
    assert directional.label == legacy.label
    assert directional.entry_timestamp == legacy.entry_timestamp
    assert directional.event_end_timestamp == legacy.event_end_timestamp
    assert directional.stop_trigger_price == legacy.stop_trigger_price
    assert directional.target_trigger_price == legacy.target_trigger_price
    assert directional.outcome_net_r == legacy.outcome_net_r


def test_short_falling_path_reaches_three_r_target():
    frame = _frame([100.0] * 70)
    frame.iloc[2, frame.columns.get_loc("Open")] = 90.0
    frame.iloc[2, frame.columns.get_loc("High")] = 90.1
    frame.iloc[2, frame.columns.get_loc("Low")] = 89.9
    outcome = directional_triple_barrier_label(
        frame,
        direction="SHORT",
        decision_position=0,
        signal_atr=2.0,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert outcome.valid is True
    assert outcome.label == "TARGET_3R_FIRST"
    assert outcome.event_end_timestamp == frame.index[2]
    assert outcome.outcome_net_r > 3.0


def test_short_rising_path_reaches_one_r_stop():
    frame = _frame([100.0] * 70)
    frame.iloc[2, frame.columns.get_loc("Open")] = 104.0
    frame.iloc[2, frame.columns.get_loc("High")] = 104.1
    frame.iloc[2, frame.columns.get_loc("Low")] = 103.9
    outcome = directional_triple_barrier_label(
        frame,
        direction="SHORT",
        decision_position=0,
        signal_atr=2.0,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert outcome.valid is True
    assert outcome.label == "STOP_1R_FIRST"
    assert outcome.outcome_net_r < -1.0


def test_short_same_bar_ambiguity_is_stop_first():
    frame = _frame([100.0] * 70)
    frame.iloc[2, frame.columns.get_loc("High")] = 104.0
    frame.iloc[2, frame.columns.get_loc("Low")] = 90.0
    outcome = directional_triple_barrier_label(
        frame,
        direction="SHORT",
        decision_position=0,
        signal_atr=2.0,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert outcome.label == "STOP_1R_FIRST"
    assert outcome.outcome_net_r == pytest.approx(-1.0)


def test_outcome_pair_uses_same_decision_and_entry_for_both_directions():
    pair = build_directional_outcome_pair(
        _frame([100.0] * 70),
        decision_position=0,
        signal_atr=2.0,
        cost_profile=ZERO_COST_PROFILE,
    )

    assert tuple(pair) == DIRECTION_ORDER
    assert pair["LONG"].decision_timestamp == pair["SHORT"].decision_timestamp
    assert pair["LONG"].entry_timestamp == pair["SHORT"].entry_timestamp


def test_provider_gap_and_right_edge_censor_both_directions():
    gap = _frame([100.0] * 70).drop(index=_frame([100.0] * 70).index[20])
    for direction in DIRECTION_ORDER:
        gap_outcome = directional_triple_barrier_label(
            gap,
            direction=direction,
            decision_position=0,
            signal_atr=2.0,
            cost_profile=ZERO_COST_PROFILE,
        )
        edge_outcome = directional_triple_barrier_label(
            _frame([100.0] * 20),
            direction=direction,
            decision_position=0,
            signal_atr=2.0,
            cost_profile=ZERO_COST_PROFILE,
        )
        assert gap_outcome.invalid_reason == "PROVIDER_GAP_CENSORED"
        assert edge_outcome.invalid_reason == "RIGHT_EDGE_CENSORED"


@pytest.mark.parametrize(
    "long_score,short_score,expected",
    [
        (0.2, -0.1, "LONG"),
        (-0.1, 0.2, "SHORT"),
        (-0.1, 0.0, "HOLD_CASH"),
        (0.2, 0.2, "HOLD_CASH"),
        (0.3, 0.2, "LONG"),
        (0.2, 0.3, "SHORT"),
    ],
)
def test_action_rule_is_fixed_positive_maximum_with_conservative_tie(
    long_score, short_score, expected
):
    assert select_bidirectional_action(long_score, short_score) == expected


def test_action_rule_rejects_nonfinite_or_non_numeric_scores():
    with pytest.raises(ValueError, match="finite"):
        select_bidirectional_action(np.nan, 0.1)
    with pytest.raises(TypeError, match="numeric"):
        select_bidirectional_action("0.1", 0.2)


def test_invalid_direction_fails_closed():
    with pytest.raises(ValueError, match="Direction"):
        directional_triple_barrier_label(
            _frame([100.0] * 70),
            direction="FLAT",
            decision_position=0,
            signal_atr=2.0,
            cost_profile=ZERO_COST_PROFILE,
        )


def test_declaration_keeps_real_learning_and_later_boundaries_closed():
    declaration = bidirectional_hypothesis_declaration()
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
    assert all(declaration[field] is False for field in required_false)


def test_protocol_freezes_symmetric_attribution_and_no_search():
    protocol = (
        ROOT
        / "KRAKEN_BTC_ETH_XRP_AI_DRIVEN_V2_BIDIRECTIONAL_DEVELOPMENT_HYPOTHESIS_PROTOCOL_V1.md"
    ).read_text(encoding="utf-8")
    normalized = " ".join(protocol.split())
    assert "No indicator is added or tuned" in normalized
    assert "same next-open entry and future path" in normalized
    assert "`LONG`: buy then sell" in normalized
    assert "`SHORT`: sell then buy to cover" in normalized
    assert "twelve fold-direction model fits" in normalized
    assert "exact positive tie returns `HOLD_CASH`" in normalized
    assert "Calibration, Evaluation, Candidate v2" in normalized

import copy
import os
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
    COST_PROFILES as ROUND_1_COST_PROFILES,
    DEVELOPMENT_SLICES as ROUND_1_DEVELOPMENT_SLICES,
    HYPOTHESIS_ORDER as ROUND_1_HYPOTHESIS_ORDER,
    ROUND_1_ROUTE_INTEREST_GATES,
    ROUND_1_SELECTION_GATES,
)
from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
    CUMULATIVE_HYPOTHESIS_COUNT,
    HYPOTHESIS_ORDER,
    PROTOCOL_ID,
    ROUND_1_CLOSURE_STATUS,
    ROUND_1_REPORT_SHA256,
    ROUND_1_ROUTE_DISPOSITIONS,
    ROUND_2_CONFIGURATION_LOCK,
    ROUND_2_HYPOTHESES,
    ROUND_2_MANIFEST_LOCK,
    ROUND_2_ROUTE_INTEREST_GATES,
    ROUND_2_SELECTION_GATES,
    ROUND_ID,
    STATUS,
    lock_round_2_configuration,
    round_2_declaration,
)
from kraken_ai_driven_v2_strategy_discovery import (
    DISCOVERY_BUDGET,
    SHARED_SAFETY_ENVELOPE,
)


EXPECTED_HYPOTHESIS_ORDER = (
    "kraken-ai-v2-r2-atr-normalized-capitulation-recovery-v1",
    "kraken-ai-v2-r2-breakout-retest-continuation-v1",
    "kraken-ai-v2-r2-trend-pullback-macd-resumption-v1",
)


def hypotheses_by_family():
    return {item["family_id"]: item for item in ROUND_2_HYPOTHESES}


def test_round_2_registers_three_feedback_derived_hypotheses_only():
    declaration = round_2_declaration()

    assert declaration["status"] == STATUS
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["round_id"] == ROUND_ID
    assert HYPOTHESIS_ORDER == EXPECTED_HYPOTHESIS_ORDER
    assert tuple(declaration["hypothesis_order"]) == EXPECTED_HYPOTHESIS_ORDER
    assert declaration["hypothesis_count"] == 3
    assert declaration["family_variant_counts"] == {
        "CAPITULATION_RECOVERY": 1,
        "TREND_PULLBACK_CONTINUATION": 1,
        "RANGE_MEAN_REVERSION": 0,
        "VOLATILITY_BREAKOUT": 1,
    }
    assert declaration["asset_route_counts"] == {
        "BTC-USD": 3,
        "ETH-USD": 3,
        "XRP-USD": 1,
    }


def test_round_2_manifest_passes_parent_validator_and_opens_nothing():
    payload = ROUND_2_MANIFEST_LOCK.payload

    assert len(ROUND_2_MANIFEST_LOCK.sha256) == 64
    assert payload["round_id"] == ROUND_ID
    assert payload["hypothesis_count"] == 3
    assert payload["asset_route_counts"] == {
        "BTC-USD": 3,
        "ETH-USD": 3,
        "XRP-USD": 1,
    }
    assert payload["development_data_access_authorized"] is False
    assert payload["round_execution_authorized"] is False
    assert payload["calibration_authorized"] is False
    assert payload["evaluation_authorized"] is False
    assert payload["candidate_v2_authorized"] is False
    assert payload["automatic_strategy_selection"] is False
    assert payload["runtime_learning_or_mutation"] is False


def test_round_2_consumes_only_three_hypothesis_slots_in_second_and_final_round():
    declaration = round_2_declaration()

    assert declaration["rounds_registered_under_protocol"] == 2
    assert declaration["maximum_rounds_under_protocol"] == 2
    assert declaration["round_1_executed_hypothesis_count"] == len(
        ROUND_1_HYPOTHESIS_ORDER
    )
    assert declaration["round_2_registered_hypothesis_count"] == 3
    assert CUMULATIVE_HYPOTHESIS_COUNT == 7
    assert declaration["cumulative_hypothesis_count"] == 7
    assert declaration["maximum_total_hypotheses_under_protocol"] == 12
    assert declaration["unused_hypothesis_capacity"] == 5
    assert declaration["unused_capacity_is_execution_authorization"] is False
    assert declaration["future_round_registered"] is False
    assert declaration["future_round_authorized"] is False
    assert CUMULATIVE_HYPOTHESIS_COUNT <= DISCOVERY_BUDGET[
        "max_total_hypotheses_under_protocol"
    ]


def test_every_round_2_hypothesis_has_exact_round_1_lineage_and_new_identity():
    round_1_ids = set(ROUND_1_HYPOTHESIS_ORDER)

    for hypothesis in ROUND_2_HYPOTHESES:
        assert hypothesis["hypothesis_id"] not in round_1_ids
        assert hypothesis["parent_hypothesis_id"] in round_1_ids
        assert hypothesis["source_feedback_sha256s"] == [ROUND_1_REPORT_SHA256]
        assert hypothesis["development_gate_id"] == (
            "kraken-ai-v2-r2-route-interest-gates-v1"
        )
        assert hypothesis["minimum_net_reward_r"] == 3.0
        assert hypothesis["causal_completed_bar_only"] is True
        assert hypothesis["next_open_entry_required"] is True
        assert hypothesis["rolling_baselines_exclude_current_bar"] is True


def test_capitulation_uses_atr_normalization_and_two_bar_stabilization():
    hypothesis = hypotheses_by_family()["CAPITULATION_RECOVERY"]

    assert hypothesis["asset_scope"] == ["BTC-USD", "ETH-USD", "XRP-USD"]
    assert hypothesis["indicator_set"] == [
        "RETURN",
        "VOLUME_RATIO",
        "ATR",
        "CLOSE_LOCATION",
    ]
    assert hypothesis["regime_parameters"] == {
        "prior_high_lookback_bars": 40,
        "drawdown_from_prior_high_atr_lte": -6.0,
        "one_bar_price_change_to_prior_atr_lte": -1.5,
        "true_range_to_prior_atr_gte": 1.75,
        "volume_to_prior_median_gte": 1.5,
        "event_close_location_lte": 0.35,
    }
    assert hypothesis["signal_parameters"] == {
        "setup_max_age_bars": 7,
        "minimum_stabilization_bars": 2,
        "confirmation_close_location_gte": 0.6,
        "confirmation_close_above_prior_2_high_required": True,
        "confirmation_volume_ratio_gte": 0.8,
    }
    assert hypothesis["execution_parameters"] == {
        "maximum_upward_gap_atr": 0.5,
        "stop_mode": "SETUP_LOW_MINUS_0_25_PRIOR_ATR",
        "target_mode": "NET_COST_ADJUSTED_FIXED_R",
        "minimum_net_reward_r": 3.0,
        "maximum_hold_bars": 25,
        "scheduled_exit": "COMPLETED_CLOSE_BELOW_PRIOR_10_CLOSE_LOW_NEXT_OPEN",
        "prior_resistance_room_gate_reused": False,
    }


def test_breakout_requires_retest_and_excludes_negative_xrp_route():
    hypothesis = hypotheses_by_family()["VOLATILITY_BREAKOUT"]

    assert hypothesis["asset_scope"] == ["BTC-USD", "ETH-USD"]
    assert hypothesis["regime_parameters"] == {
        "donchian_prior_high_period": 55,
        "atr_period": 14,
        "atr_baseline_bars": 60,
        "atr_to_prior_median_gte": 1.1,
        "adx_period": 14,
        "adx_gte": 20.0,
    }
    assert hypothesis["signal_parameters"] == {
        "setup_close_above_prior_55_high_required": True,
        "setup_volume_ratio_gte": 1.25,
        "setup_close_location_gte": 0.7,
        "retest_window_bars": 5,
        "retest_low_to_breakout_level_atr_lte": 0.25,
        "retest_close_at_or_above_breakout_level_required": True,
        "confirmation_close_above_prior_high_required": True,
        "confirmation_volume_ratio_gte": 1.0,
    }
    assert hypothesis["execution_parameters"]["stop_mode"] == (
        "RETEST_LOW_MINUS_0_25_PRIOR_ATR"
    )
    assert hypothesis["execution_parameters"]["maximum_hold_bars"] == 60
    assert hypothesis["direct_breakout_entry_reused"] is False


def test_trend_requires_multibar_pullback_and_macd_resumption_without_xrp():
    hypothesis = hypotheses_by_family()["TREND_PULLBACK_CONTINUATION"]

    assert hypothesis["asset_scope"] == ["BTC-USD", "ETH-USD"]
    assert hypothesis["indicator_set"] == [
        "EMA",
        "ADX",
        "MACD",
        "VOLUME_RATIO",
        "ATR",
    ]
    assert hypothesis["regime_parameters"] == {
        "pullback_ema_period": 20,
        "trend_ema_period": 50,
        "slow_ema_period": 200,
        "trend_slope_lookback_bars": 20,
        "adx_period": 14,
        "adx_gte": 20.0,
    }
    assert hypothesis["signal_parameters"] == {
        "pullback_min_age_bars": 2,
        "pullback_max_age_bars": 5,
        "pullback_low_to_ema20_atr_lte": 0.5,
        "pullback_close_above_ema50_required": True,
        "pullback_volume_ratio_lte": 1.0,
        "macd_histogram_nonpositive_seen_required": True,
        "confirmation_macd_histogram_cross_above_zero_required": True,
        "confirmation_close_above_prior_3_high_required": True,
        "confirmation_volume_ratio_gte": 1.0,
    }
    assert hypothesis["execution_parameters"]["stop_mode"] == (
        "PULLBACK_LOW_MINUS_0_25_PRIOR_ATR"
    )
    assert hypothesis["execution_parameters"]["maximum_hold_bars"] == 40


def test_round_1_dispositions_retire_unsupported_routes_without_ranking():
    assert ROUND_1_ROUTE_DISPOSITIONS == {
        "BTC-USD|VOLATILITY_BREAKOUT": "REPLACE_WITH_BREAKOUT_RETEST_VARIANT",
        "ETH-USD|VOLATILITY_BREAKOUT": "REPLACE_WITH_BREAKOUT_RETEST_VARIANT",
        "BTC-USD|CAPITULATION_RECOVERY": "REPLACE_WITH_ATR_NORMALIZED_VARIANT",
        "ETH-USD|CAPITULATION_RECOVERY": "REPLACE_WITH_ATR_NORMALIZED_VARIANT",
        "XRP-USD|CAPITULATION_RECOVERY": "REPLACE_WITH_ATR_NORMALIZED_VARIANT",
        "BTC-USD|TREND_PULLBACK_CONTINUATION": (
            "REPLACE_WITH_MULTIBAR_MACD_VARIANT"
        ),
        "ETH-USD|TREND_PULLBACK_CONTINUATION": (
            "REPLACE_WITH_MULTIBAR_MACD_VARIANT"
        ),
        "XRP-USD|TREND_PULLBACK_CONTINUATION": (
            "RETIRED_NEGATIVE_EXPECTANCY_BOTH_COST_PROFILES"
        ),
        "BTC-USD|RANGE_MEAN_REVERSION": "RETIRED_NO_CLOSED_TRADE_EVIDENCE",
        "ETH-USD|RANGE_MEAN_REVERSION": "RETIRED_NO_CLOSED_TRADE_EVIDENCE",
        "XRP-USD|RANGE_MEAN_REVERSION": "RETIRED_NO_CLOSED_TRADE_EVIDENCE",
        "XRP-USD|VOLATILITY_BREAKOUT": (
            "RETIRED_NEGATIVE_EXPECTANCY_BOTH_COST_PROFILES"
        ),
    }
    declaration = round_2_declaration()
    assert declaration["automatic_ranking_generated"] is False
    assert declaration["automatic_strategy_selection_authorized"] is False


def test_round_2_does_not_weaken_costs_slices_gates_or_safety_envelope():
    declaration = round_2_declaration()

    assert declaration["cost_profiles"] == ROUND_1_COST_PROFILES
    assert declaration["development_slices"] == [
        {"slice_id": item[0], "start_utc": item[1], "end_exclusive_utc": item[2]}
        for item in ROUND_1_DEVELOPMENT_SLICES
    ]
    assert ROUND_2_ROUTE_INTEREST_GATES == ROUND_1_ROUTE_INTEREST_GATES
    assert ROUND_2_SELECTION_GATES == ROUND_1_SELECTION_GATES
    assert declaration["shared_safety_envelope"] == SHARED_SAFETY_ENVELOPE
    assert declaration["round_1_gates_weakened"] is False
    assert declaration["cost_profiles_changed"] is False
    assert declaration["development_slices_changed"] is False


def test_configuration_lock_is_deterministic_and_rejects_post_registration_change():
    first = lock_round_2_configuration()
    second = lock_round_2_configuration(copy.deepcopy(first.payload))

    assert first == second == ROUND_2_CONFIGURATION_LOCK
    assert len(first.sha256) == 64
    changed = copy.deepcopy(first.payload)
    changed["hypotheses"][0]["signal_parameters"][
        "setup_max_age_bars"
    ] = 8
    with pytest.raises(ValueError, match="configuration mismatch"):
        lock_round_2_configuration(changed)


def test_declaration_is_an_independent_copy_of_frozen_configuration():
    first = round_2_declaration()
    first["hypotheses"][0]["asset_scope"].append("CHANGED")
    first["round_1_route_dispositions"]["CHANGED"] = "CHANGED"
    second = round_2_declaration()

    assert second["hypotheses"][0]["asset_scope"] == [
        "BTC-USD",
        "ETH-USD",
        "XRP-USD",
    ]
    assert "CHANGED" not in second["round_1_route_dispositions"]


def test_round_2_registration_authorizes_no_data_component_or_execution():
    declaration = round_2_declaration()

    assert declaration["round_1_closure_status"] == ROUND_1_CLOSURE_STATUS
    assert declaration["round_1_report_sha256"] == ROUND_1_REPORT_SHA256
    assert declaration["round_1_closed"] is True
    assert declaration["round_1_rerun_authorized"] is False
    assert declaration["round_2_manifest_registered"] is True
    for field in (
        "regime_components_implemented",
        "signal_components_implemented",
        "execution_components_implemented",
        "discovery_runner_implemented",
        "dataset_opened",
        "development_data_opened",
        "calibration_data_opened",
        "evaluation_data_opened",
        "development_run_authorized",
        "performance_evaluation_executed",
        "parameter_sweep_authorized",
        "automatic_ranking_authorized",
        "automatic_strategy_selection_authorized",
        "runtime_learning_authorized",
        "calibration_authorized",
        "evaluation_authorized",
        "candidate_v2_authorized",
        "bounded_forward_paper_authorized",
        "cloud_execution_authorized",
        "live_execution_authorized",
    ):
        assert declaration[field] is False
    assert declaration["next_stage"] == (
        "IMPLEMENT_ROUND_2_CAUSAL_COMPONENTS_SYNTHETIC_ONLY"
    )

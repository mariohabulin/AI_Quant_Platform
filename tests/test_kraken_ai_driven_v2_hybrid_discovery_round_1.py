import copy
import os
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
    ASSET_ORDER,
    COST_PROFILES,
    DEVELOPMENT_SLICES,
    HYPOTHESIS_ORDER,
    PROTOCOL_ID,
    ROUND_1_HYPOTHESES,
    ROUND_1_MANIFEST_LOCK,
    ROUND_1_ROUTE_INTEREST_GATES,
    ROUND_1_SELECTION_GATES,
    ROUND_ID,
    STATUS,
    lock_round_1_configuration,
    round_1_declaration,
)
from kraken_ai_driven_v2_strategy_discovery import (
    REFERENCE_A_REPORT_SHA256,
    SHARED_SAFETY_ENVELOPE,
)


EXPECTED_HYPOTHESIS_ORDER = (
    "kraken-ai-v2-r1-capitulation-recovery-volatility-path-v1",
    "kraken-ai-v2-r1-trend-pullback-continuation-v1",
    "kraken-ai-v2-r1-range-mean-reversion-v1",
    "kraken-ai-v2-r1-volatility-breakout-v1",
)


def hypotheses_by_family():
    return {item["family_id"]: item for item in ROUND_1_HYPOTHESES}


def test_round_1_registers_exactly_one_hypothesis_per_family_for_all_assets():
    declaration = round_1_declaration()

    assert declaration["status"] == STATUS
    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["round_id"] == ROUND_ID
    assert tuple(declaration["hypothesis_order"]) == EXPECTED_HYPOTHESIS_ORDER
    assert HYPOTHESIS_ORDER == EXPECTED_HYPOTHESIS_ORDER
    assert declaration["hypothesis_count"] == 4
    assert declaration["family_variant_counts"] == {
        "CAPITULATION_RECOVERY": 1,
        "TREND_PULLBACK_CONTINUATION": 1,
        "RANGE_MEAN_REVERSION": 1,
        "VOLATILITY_BREAKOUT": 1,
    }
    assert declaration["asset_route_counts"] == {
        "BTC-USD": 4,
        "ETH-USD": 4,
        "XRP-USD": 4,
    }
    for hypothesis in declaration["hypotheses"]:
        assert hypothesis["asset_scope"] == list(ASSET_ORDER)
        assert hypothesis["minimum_net_reward_r"] == 3.0
        assert hypothesis["causal_completed_bar_only"] is True
        assert hypothesis["next_open_entry_required"] is True


def test_round_1_manifest_passes_parent_hybrid_validator_and_is_locked():
    payload = ROUND_1_MANIFEST_LOCK.payload

    assert len(ROUND_1_MANIFEST_LOCK.sha256) == 64
    assert payload["round_id"] == ROUND_ID
    assert payload["hypothesis_count"] == 4
    assert payload["asset_route_counts"] == {
        "BTC-USD": 4,
        "ETH-USD": 4,
        "XRP-USD": 4,
    }
    assert payload["automatic_strategy_selection"] is False
    assert payload["runtime_learning_or_mutation"] is False
    assert payload["round_execution_authorized"] is False
    assert payload["calibration_authorized"] is False
    assert payload["evaluation_authorized"] is False
    assert payload["candidate_v2_authorized"] is False


def test_capitulation_recovery_is_structurally_new_and_reference_a_is_lineage_only():
    hypothesis = hypotheses_by_family()["CAPITULATION_RECOVERY"]

    assert hypothesis["hypothesis_id"] == EXPECTED_HYPOTHESIS_ORDER[0]
    assert hypothesis["source_feedback_sha256s"] == [
        REFERENCE_A_REPORT_SHA256
    ]
    assert hypothesis["regime_parameters"] == {
        "drawdown_60_fraction_lte": -0.18,
        "one_bar_return_fraction_lte": -0.06,
        "true_range_to_prior_atr_gte": 1.5,
        "volume_to_prior_median_gte": 1.5,
        "event_close_location_lte": 0.35,
    }
    assert hypothesis["signal_parameters"]["setup_max_age_bars"] == 5
    assert hypothesis["signal_parameters"]["confirmation_close_location_gte"] == 0.65
    assert hypothesis["execution_parameters"] == {
        "maximum_upward_gap_atr": 0.5,
        "stop_mode": "SETUP_LOW_MINUS_0_25_PRIOR_ATR",
        "target_mode": "NET_COST_ADJUSTED_FIXED_R",
        "minimum_net_reward_r": 3.0,
        "maximum_hold_bars": 20,
        "scheduled_exit": "COMPLETED_CLOSE_BELOW_PRIOR_10_CLOSE_LOW_NEXT_OPEN",
        "prior_resistance_room_gate_reused": False,
    }


def test_trend_pullback_has_exact_causal_trend_and_reexpansion_contract():
    hypothesis = hypotheses_by_family()["TREND_PULLBACK_CONTINUATION"]

    assert hypothesis["regime_parameters"] == {
        "pullback_ema_period": 20,
        "trend_ema_period": 50,
        "slow_ema_period": 200,
        "trend_slope_lookback_bars": 20,
        "adx_period": 14,
        "adx_gte": 20.0,
    }
    assert hypothesis["signal_parameters"] == {
        "pullback_low_to_ema20_atr_lte": 0.25,
        "pullback_close_above_ema50_required": True,
        "pullback_volume_ratio_lte": 0.9,
        "confirmation_close_above_prior_high_required": True,
        "confirmation_close_above_ema20_required": True,
        "confirmation_volume_ratio_gte": 1.1,
    }
    assert hypothesis["execution_parameters"]["maximum_hold_bars"] == 40
    assert hypothesis["execution_parameters"]["stop_mode"] == (
        "PULLBACK_LOW_MINUS_0_25_PRIOR_ATR"
    )


def test_range_reversion_targets_signal_time_midband_with_three_r_room():
    hypothesis = hypotheses_by_family()["RANGE_MEAN_REVERSION"]

    assert hypothesis["regime_parameters"] == {
        "bollinger_period": 20,
        "bollinger_standard_deviations": 2.0,
        "band_width_baseline_bars": 120,
        "band_width_to_prior_median_lte": 1.1,
        "atr_period": 14,
        "atr_to_prior_median_lte": 1.1,
    }
    assert hypothesis["signal_parameters"]["setup_rsi_lte"] == 25.0
    assert hypothesis["signal_parameters"]["setup_stochastic_k_lte"] == 20.0
    assert hypothesis["execution_parameters"]["target_mode"] == (
        "SIGNAL_TIME_BOLLINGER_MIDLINE_WITH_NET_3R_ROOM"
    )
    assert hypothesis["execution_parameters"]["maximum_hold_bars"] == 15


def test_breakout_uses_prior_channel_expansion_and_no_current_bar_baseline():
    hypothesis = hypotheses_by_family()["VOLATILITY_BREAKOUT"]

    assert hypothesis["regime_parameters"] == {
        "donchian_prior_high_period": 55,
        "atr_period": 14,
        "atr_baseline_bars": 60,
        "atr_to_prior_median_gte": 1.1,
        "adx_period": 14,
        "adx_gte": 20.0,
    }
    assert hypothesis["signal_parameters"] == {
        "close_above_prior_55_high_required": True,
        "volume_ratio_gte": 1.25,
        "close_location_gte": 0.7,
    }
    assert hypothesis["execution_parameters"]["stop_mode"] == (
        "MAX_BREAKOUT_LOW_MINUS_0_25_ATR_OR_ENTRY_MINUS_2_ATR"
    )
    assert hypothesis["execution_parameters"]["maximum_hold_bars"] == 60
    assert hypothesis["rolling_baselines_exclude_current_bar"] is True


def test_cost_profiles_preserve_official_commission_and_double_research_frictions():
    assert COST_PROFILES == {
        "baseline": {
            "cost_profile_id": "kraken-tier1-taker-adverse-20260829-v1",
            "commission_per_side_fraction": 0.008,
            "slippage_per_side_fraction": 0.0015,
            "full_spread_fraction": 0.003,
        },
        "stress": {
            "cost_profile_id": "kraken-tier1-taker-adverse-stress-r1-v1",
            "commission_per_side_fraction": 0.008,
            "slippage_per_side_fraction": 0.003,
            "full_spread_fraction": 0.006,
        },
    }


def test_route_interest_gates_are_absolute_and_not_a_return_leaderboard():
    assert ROUND_1_ROUTE_INTEREST_GATES == {
        "minimum_closed_trades": 8,
        "minimum_slices_with_trade": 3,
        "minimum_nonnegative_slices": 3,
        "minimum_baseline_net_expectancy_r": 0.1,
        "minimum_stress_net_expectancy_r": 0.0,
        "minimum_baseline_profit_factor": 1.2,
        "minimum_stress_profit_factor": 1.0,
        "maximum_baseline_marked_drawdown_fraction": 0.12,
        "maximum_stress_marked_drawdown_fraction": 0.18,
        "maximum_largest_trade_net_profit_share": 0.4,
        "required_unresolved_position_count": 0,
    }
    assert ROUND_1_SELECTION_GATES == {
        "minimum_eligible_asset_count": 2,
        "minimum_eligible_route_count": 2,
        "same_asset_multiple_pass_action": "SEPARATE_PORTFOLIO_REVIEW_REQUIRED",
        "automatic_winner_selection": False,
        "cross_asset_portability_is_diagnostic_only": True,
        "failed_route_action": "HOLD_CASH",
    }


def test_development_slices_are_fixed_before_data_access():
    assert DEVELOPMENT_SLICES == (
        ("D1", "2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z"),
        ("D2", "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z"),
        ("D3", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z"),
        ("D4", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
        ("D5", "2023-01-01T00:00:00Z", "2024-04-01T00:00:00Z"),
    )


def test_configuration_lock_is_deterministic_and_rejects_post_registration_change():
    first = lock_round_1_configuration()
    second = lock_round_1_configuration(copy.deepcopy(first.payload))

    assert first == second
    assert len(first.sha256) == 64
    changed = copy.deepcopy(first.payload)
    changed["hypotheses"][0]["execution_parameters"][
        "minimum_net_reward_r"
    ] = 2.0
    with pytest.raises(ValueError, match="configuration mismatch"):
        lock_round_1_configuration(changed)


def test_declaration_is_an_independent_copy_of_frozen_configuration():
    first = round_1_declaration()
    first["hypotheses"][0]["asset_scope"].append("CHANGED")
    first["shared_safety_envelope"]["position_risk_fraction_ceiling"] = 1.0
    second = round_1_declaration()

    assert second["hypotheses"][0]["asset_scope"] == list(ASSET_ORDER)
    assert second["shared_safety_envelope"] == SHARED_SAFETY_ENVELOPE


def test_round_1_is_registration_only_and_authorizes_nothing():
    declaration = round_1_declaration()

    assert declaration["hypothesis_manifest_registered"] is True
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

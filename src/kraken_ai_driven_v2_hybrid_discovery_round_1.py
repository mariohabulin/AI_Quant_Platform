"""Pre-registered, nonexecuting Kraken V2 hybrid discovery Round 1."""

import copy
from dataclasses import dataclass
import hashlib
import json

try:
    from kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        PROTOCOL_ID as PARENT_PROTOCOL_ID,
        REFERENCE_A_REPORT_SHA256,
        REFERENCE_A_SIGNAL_CONTRACT_ID,
        SHARED_SAFETY_ENVELOPE,
        validate_hypothesis_manifest,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        PROTOCOL_ID as PARENT_PROTOCOL_ID,
        REFERENCE_A_REPORT_SHA256,
        REFERENCE_A_SIGNAL_CONTRACT_ID,
        SHARED_SAFETY_ENVELOPE,
        validate_hypothesis_manifest,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1"
ROUND_ID = "kraken-ai-v2-hybrid-discovery-round-1"
STATUS = (
    "KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_1_"
    "PRE_REGISTERED_COMPONENTS_REQUIRED"
)
DEVELOPMENT_GATE_ID = "kraken-ai-v2-r1-route-interest-gates-v1"

HYPOTHESIS_ORDER = (
    "kraken-ai-v2-r1-capitulation-recovery-volatility-path-v1",
    "kraken-ai-v2-r1-trend-pullback-continuation-v1",
    "kraken-ai-v2-r1-range-mean-reversion-v1",
    "kraken-ai-v2-r1-volatility-breakout-v1",
)

DEVELOPMENT_SLICES = (
    ("D1", "2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z"),
    ("D2", "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z"),
    ("D3", "2021-01-01T00:00:00Z", "2022-01-01T00:00:00Z"),
    ("D4", "2022-01-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("D5", "2023-01-01T00:00:00Z", "2024-04-01T00:00:00Z"),
)

COST_PROFILES = {
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

ROUND_1_ROUTE_INTEREST_GATES = {
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

ROUND_1_SELECTION_GATES = {
    "minimum_eligible_asset_count": 2,
    "minimum_eligible_route_count": 2,
    "same_asset_multiple_pass_action": "SEPARATE_PORTFOLIO_REVIEW_REQUIRED",
    "automatic_winner_selection": False,
    "cross_asset_portability_is_diagnostic_only": True,
    "failed_route_action": "HOLD_CASH",
}

_ROUND_1_HYPOTHESES = (
    {
        "hypothesis_id": HYPOTHESIS_ORDER[0],
        "family_id": "CAPITULATION_RECOVERY",
        "asset_scope": list(ASSET_ORDER),
        "regime_scope": ["DOWNTREND_CAPITULATION"],
        "indicator_set": ["RETURN", "VOLUME_RATIO", "ATR", "CLOSE_LOCATION"],
        "economic_thesis": (
            "A volatility-normalized capitulation followed by completed-bar "
            "stabilization may support a net cost-adjusted three-R recovery path."
        ),
        "signal_contract_id": "kraken-ai-v2-r1-capitulation-signal-v1",
        "execution_contract_id": "kraken-ai-v2-r1-capitulation-execution-v1",
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": REFERENCE_A_SIGNAL_CONTRACT_ID,
        "source_feedback_sha256s": [REFERENCE_A_REPORT_SHA256],
        "regime_parameters": {
            "drawdown_60_fraction_lte": -0.18,
            "one_bar_return_fraction_lte": -0.06,
            "true_range_to_prior_atr_gte": 1.5,
            "volume_to_prior_median_gte": 1.5,
            "event_close_location_lte": 0.35,
        },
        "signal_parameters": {
            "setup_max_age_bars": 5,
            "confirmation_close_location_gte": 0.65,
            "confirmation_return_gt": 0.0,
            "confirmation_volume_ratio_gte": 0.8,
            "confirmation_close_above_prior_high_required": True,
        },
        "execution_parameters": {
            "maximum_upward_gap_atr": 0.5,
            "stop_mode": "SETUP_LOW_MINUS_0_25_PRIOR_ATR",
            "target_mode": "NET_COST_ADJUSTED_FIXED_R",
            "minimum_net_reward_r": 3.0,
            "maximum_hold_bars": 20,
            "scheduled_exit": (
                "COMPLETED_CLOSE_BELOW_PRIOR_10_CLOSE_LOW_NEXT_OPEN"
            ),
            "prior_resistance_room_gate_reused": False,
        },
        "minimum_net_reward_r": 3.0,
        "causal_completed_bar_only": True,
        "next_open_entry_required": True,
        "rolling_baselines_exclude_current_bar": True,
    },
    {
        "hypothesis_id": HYPOTHESIS_ORDER[1],
        "family_id": "TREND_PULLBACK_CONTINUATION",
        "asset_scope": list(ASSET_ORDER),
        "regime_scope": ["UPTREND_PULLBACK"],
        "indicator_set": ["EMA", "ADX", "VOLUME_RATIO", "ATR"],
        "economic_thesis": (
            "A low-volume pullback inside a positive causal trend may resume "
            "after a completed-bar price and volume re-expansion confirmation."
        ),
        "signal_contract_id": "kraken-ai-v2-r1-trend-pullback-signal-v1",
        "execution_contract_id": "kraken-ai-v2-r1-trend-pullback-execution-v1",
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": None,
        "source_feedback_sha256s": [],
        "regime_parameters": {
            "pullback_ema_period": 20,
            "trend_ema_period": 50,
            "slow_ema_period": 200,
            "trend_slope_lookback_bars": 20,
            "adx_period": 14,
            "adx_gte": 20.0,
        },
        "signal_parameters": {
            "pullback_low_to_ema20_atr_lte": 0.25,
            "pullback_close_above_ema50_required": True,
            "pullback_volume_ratio_lte": 0.9,
            "confirmation_close_above_prior_high_required": True,
            "confirmation_close_above_ema20_required": True,
            "confirmation_volume_ratio_gte": 1.1,
        },
        "execution_parameters": {
            "maximum_upward_gap_atr": 0.5,
            "stop_mode": "PULLBACK_LOW_MINUS_0_25_PRIOR_ATR",
            "target_mode": "NET_COST_ADJUSTED_FIXED_R",
            "minimum_net_reward_r": 3.0,
            "maximum_hold_bars": 40,
            "scheduled_exit": "COMPLETED_CLOSE_BELOW_EMA50_NEXT_OPEN",
        },
        "minimum_net_reward_r": 3.0,
        "causal_completed_bar_only": True,
        "next_open_entry_required": True,
        "rolling_baselines_exclude_current_bar": True,
    },
    {
        "hypothesis_id": HYPOTHESIS_ORDER[2],
        "family_id": "RANGE_MEAN_REVERSION",
        "asset_scope": list(ASSET_ORDER),
        "regime_scope": ["RANGE_BOUND"],
        "indicator_set": ["RSI", "BOLLINGER_BANDS", "STOCHASTIC", "ATR"],
        "economic_thesis": (
            "A volatility-bounded range extreme may revert toward its causal "
            "signal-time center after momentum and band re-entry confirmation."
        ),
        "signal_contract_id": "kraken-ai-v2-r1-range-reversion-signal-v1",
        "execution_contract_id": "kraken-ai-v2-r1-range-reversion-execution-v1",
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": None,
        "source_feedback_sha256s": [],
        "regime_parameters": {
            "bollinger_period": 20,
            "bollinger_standard_deviations": 2.0,
            "band_width_baseline_bars": 120,
            "band_width_to_prior_median_lte": 1.1,
            "atr_period": 14,
            "atr_to_prior_median_lte": 1.1,
        },
        "signal_parameters": {
            "setup_close_below_lower_band_required": True,
            "setup_rsi_lte": 25.0,
            "setup_stochastic_k_lte": 20.0,
            "confirmation_close_back_inside_band_required": True,
            "confirmation_rsi_rising_required": True,
            "confirmation_stochastic_k_cross_above_d_required": True,
        },
        "execution_parameters": {
            "maximum_upward_gap_atr": 0.5,
            "stop_mode": "SETUP_LOW_MINUS_0_25_PRIOR_ATR",
            "target_mode": "SIGNAL_TIME_BOLLINGER_MIDLINE_WITH_NET_3R_ROOM",
            "minimum_net_reward_r": 3.0,
            "maximum_hold_bars": 15,
            "scheduled_exit": "SIGNAL_TIME_MIDLINE_OR_MAX_HOLD_NEXT_OPEN",
        },
        "minimum_net_reward_r": 3.0,
        "causal_completed_bar_only": True,
        "next_open_entry_required": True,
        "rolling_baselines_exclude_current_bar": True,
    },
    {
        "hypothesis_id": HYPOTHESIS_ORDER[3],
        "family_id": "VOLATILITY_BREAKOUT",
        "asset_scope": list(ASSET_ORDER),
        "regime_scope": ["VOLATILITY_EXPANSION"],
        "indicator_set": [
            "DONCHIAN_CHANNEL",
            "ATR",
            "VOLUME_RATIO",
            "CLOSE_LOCATION",
            "ADX",
        ],
        "economic_thesis": (
            "A completed-bar break above the prior channel with trend, volume "
            "and volatility expansion may sustain a net three-R continuation."
        ),
        "signal_contract_id": "kraken-ai-v2-r1-breakout-signal-v1",
        "execution_contract_id": "kraken-ai-v2-r1-breakout-execution-v1",
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": None,
        "source_feedback_sha256s": [],
        "regime_parameters": {
            "donchian_prior_high_period": 55,
            "atr_period": 14,
            "atr_baseline_bars": 60,
            "atr_to_prior_median_gte": 1.1,
            "adx_period": 14,
            "adx_gte": 20.0,
        },
        "signal_parameters": {
            "close_above_prior_55_high_required": True,
            "volume_ratio_gte": 1.25,
            "close_location_gte": 0.7,
        },
        "execution_parameters": {
            "maximum_upward_gap_atr": 0.5,
            "stop_mode": (
                "MAX_BREAKOUT_LOW_MINUS_0_25_ATR_OR_ENTRY_MINUS_2_ATR"
            ),
            "target_mode": "NET_COST_ADJUSTED_FIXED_R",
            "minimum_net_reward_r": 3.0,
            "maximum_hold_bars": 60,
            "scheduled_exit": (
                "COMPLETED_CLOSE_BELOW_PRIOR_10_CLOSE_LOW_NEXT_OPEN"
            ),
        },
        "minimum_net_reward_r": 3.0,
        "causal_completed_bar_only": True,
        "next_open_entry_required": True,
        "rolling_baselines_exclude_current_bar": True,
    },
)

ROUND_1_HYPOTHESES = copy.deepcopy(_ROUND_1_HYPOTHESES)


def _manifest_hypothesis(hypothesis):
    fields = (
        "hypothesis_id",
        "family_id",
        "asset_scope",
        "regime_scope",
        "indicator_set",
        "economic_thesis",
        "signal_contract_id",
        "execution_contract_id",
        "development_gate_id",
        "parent_hypothesis_id",
        "source_feedback_sha256s",
    )
    return {field: copy.deepcopy(hypothesis[field]) for field in fields}


ROUND_1_MANIFEST = {
    "schema_version": SCHEMA_VERSION,
    "protocol_id": PARENT_PROTOCOL_ID,
    "round_id": ROUND_ID,
    "partition": "DEVELOPMENT",
    "hypotheses": [
        _manifest_hypothesis(hypothesis)
        for hypothesis in _ROUND_1_HYPOTHESES
    ],
    "development_data_access_authorized": False,
    "calibration_authorized": False,
    "evaluation_authorized": False,
    "automatic_mutation_authorized": False,
    "automatic_ranking_authorized": False,
    "candidate_v2_authorized": False,
    "round_execution_authorized": False,
}
ROUND_1_MANIFEST_LOCK = validate_hypothesis_manifest(ROUND_1_MANIFEST)


@dataclass(frozen=True)
class LockedRound1Configuration:
    payload: dict
    sha256: str


def _canonical_json_bytes(value):
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("Round 1 configuration must be canonical JSON data.") from exc


def _reference_configuration():
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "parent_protocol_id": PARENT_PROTOCOL_ID,
        "round_id": ROUND_ID,
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "hypothesis_order": list(HYPOTHESIS_ORDER),
        "hypotheses": copy.deepcopy(_ROUND_1_HYPOTHESES),
        "manifest_sha256": ROUND_1_MANIFEST_LOCK.sha256,
        "development_slices": [
            {"slice_id": item[0], "start_utc": item[1], "end_exclusive_utc": item[2]}
            for item in DEVELOPMENT_SLICES
        ],
        "cost_profiles": copy.deepcopy(COST_PROFILES),
        "shared_safety_envelope": copy.deepcopy(SHARED_SAFETY_ENVELOPE),
        "route_interest_gates": copy.deepcopy(ROUND_1_ROUTE_INTEREST_GATES),
        "selection_gates": copy.deepcopy(ROUND_1_SELECTION_GATES),
        "gap_and_partition_context_reset_required": True,
        "route_evaluation_unit": "ASSET_FAMILY_PAIR",
        "performance_comparison_policy": "ABSOLUTE_GATES_NO_LEADERBOARD",
        "same_asset_multiple_pass_policy": "SEPARATE_PORTFOLIO_REVIEW_REQUIRED",
    }


_REFERENCE_CONFIGURATION = _reference_configuration()


def lock_round_1_configuration(configuration=None):
    """Lock the exact pre-registered configuration without opening data."""

    candidate = copy.deepcopy(
        _REFERENCE_CONFIGURATION if configuration is None else configuration
    )
    if candidate != _REFERENCE_CONFIGURATION:
        raise ValueError("Round 1 configuration mismatch after pre-registration.")
    digest = hashlib.sha256(_canonical_json_bytes(candidate)).hexdigest()
    return LockedRound1Configuration(payload=candidate, sha256=digest)


ROUND_1_CONFIGURATION_LOCK = lock_round_1_configuration()


def round_1_declaration():
    """Return the frozen Round 1 registration and explicit nonauthorization."""

    declaration = copy.deepcopy(ROUND_1_CONFIGURATION_LOCK.payload)
    declaration.update(
        {
            "configuration_sha256": ROUND_1_CONFIGURATION_LOCK.sha256,
            "hypothesis_count": ROUND_1_MANIFEST_LOCK.payload["hypothesis_count"],
            "family_variant_counts": copy.deepcopy(
                ROUND_1_MANIFEST_LOCK.payload["family_variant_counts"]
            ),
            "asset_route_counts": copy.deepcopy(
                ROUND_1_MANIFEST_LOCK.payload["asset_route_counts"]
            ),
            "hypothesis_manifest_registered": True,
            "regime_components_implemented": False,
            "signal_components_implemented": False,
            "execution_components_implemented": False,
            "discovery_runner_implemented": False,
            "dataset_opened": False,
            "development_data_opened": False,
            "calibration_data_opened": False,
            "evaluation_data_opened": False,
            "development_run_authorized": False,
            "performance_evaluation_executed": False,
            "parameter_sweep_authorized": False,
            "automatic_ranking_authorized": False,
            "automatic_strategy_selection_authorized": False,
            "runtime_learning_authorized": False,
            "calibration_authorized": False,
            "evaluation_authorized": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
            "next_stage": "IMPLEMENT_ROUND_1_CAUSAL_COMPONENTS_SYNTHETIC_ONLY",
        }
    )
    return declaration

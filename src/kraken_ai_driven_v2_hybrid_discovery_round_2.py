"""Pre-registered, nonexecuting Kraken V2 hybrid discovery Round 2."""

import copy
from dataclasses import dataclass
import hashlib
import json

try:
    from kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        COST_PROFILES,
        DEVELOPMENT_SLICES,
        HYPOTHESIS_ORDER as ROUND_1_HYPOTHESIS_ORDER,
        PROTOCOL_ID as ROUND_1_PROTOCOL_ID,
        ROUND_1_ROUTE_INTEREST_GATES,
        ROUND_1_SELECTION_GATES,
    )
    from kraken_ai_driven_v2_round_1_closure import (
        CLOSURE_STATUS as ROUND_1_CLOSURE_STATUS,
        RECORDED_REPORT_SHA256 as ROUND_1_REPORT_SHA256,
    )
    from kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        DISCOVERY_BUDGET,
        PROTOCOL_ID as PARENT_PROTOCOL_ID,
        SHARED_SAFETY_ENVELOPE,
        validate_hypothesis_manifest,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_ai_driven_v2_hybrid_discovery_round_1 import (
        COST_PROFILES,
        DEVELOPMENT_SLICES,
        HYPOTHESIS_ORDER as ROUND_1_HYPOTHESIS_ORDER,
        PROTOCOL_ID as ROUND_1_PROTOCOL_ID,
        ROUND_1_ROUTE_INTEREST_GATES,
        ROUND_1_SELECTION_GATES,
    )
    from .kraken_ai_driven_v2_round_1_closure import (
        CLOSURE_STATUS as ROUND_1_CLOSURE_STATUS,
        RECORDED_REPORT_SHA256 as ROUND_1_REPORT_SHA256,
    )
    from .kraken_ai_driven_v2_strategy_discovery import (
        ASSET_ORDER,
        DISCOVERY_BUDGET,
        PROTOCOL_ID as PARENT_PROTOCOL_ID,
        SHARED_SAFETY_ENVELOPE,
        validate_hypothesis_manifest,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1"
ROUND_ID = "kraken-ai-v2-hybrid-discovery-round-2"
STATUS = (
    "KRAKEN_AI_V2_HYBRID_DISCOVERY_ROUND_2_"
    "PRE_REGISTERED_COMPONENTS_REQUIRED"
)
DEVELOPMENT_GATE_ID = "kraken-ai-v2-r2-route-interest-gates-v1"

HYPOTHESIS_ORDER = (
    "kraken-ai-v2-r2-atr-normalized-capitulation-recovery-v1",
    "kraken-ai-v2-r2-breakout-retest-continuation-v1",
    "kraken-ai-v2-r2-trend-pullback-macd-resumption-v1",
)

ROUND_2_ROUTE_INTEREST_GATES = copy.deepcopy(ROUND_1_ROUTE_INTEREST_GATES)
ROUND_2_SELECTION_GATES = copy.deepcopy(ROUND_1_SELECTION_GATES)

ROUND_1_ROUTE_DISPOSITIONS = {
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

_ROUND_2_HYPOTHESES = (
    {
        "hypothesis_id": HYPOTHESIS_ORDER[0],
        "family_id": "CAPITULATION_RECOVERY",
        "asset_scope": list(ASSET_ORDER),
        "regime_scope": ["DOWNTREND_CAPITULATION"],
        "indicator_set": ["RETURN", "VOLUME_RATIO", "ATR", "CLOSE_LOCATION"],
        "economic_thesis": (
            "An ATR-normalized decline and shock followed by two completed "
            "stabilization bars may identify transferable recovery paths without "
            "forcing identical percentage thresholds across BTC, ETH and XRP."
        ),
        "signal_contract_id": "kraken-ai-v2-r2-atr-capitulation-signal-v1",
        "execution_contract_id": "kraken-ai-v2-r2-atr-capitulation-execution-v1",
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": ROUND_1_HYPOTHESIS_ORDER[0],
        "source_feedback_sha256s": [ROUND_1_REPORT_SHA256],
        "regime_parameters": {
            "prior_high_lookback_bars": 40,
            "drawdown_from_prior_high_atr_lte": -6.0,
            "one_bar_price_change_to_prior_atr_lte": -1.5,
            "true_range_to_prior_atr_gte": 1.75,
            "volume_to_prior_median_gte": 1.5,
            "event_close_location_lte": 0.35,
        },
        "signal_parameters": {
            "setup_max_age_bars": 7,
            "minimum_stabilization_bars": 2,
            "confirmation_close_location_gte": 0.6,
            "confirmation_close_above_prior_2_high_required": True,
            "confirmation_volume_ratio_gte": 0.8,
        },
        "execution_parameters": {
            "maximum_upward_gap_atr": 0.5,
            "stop_mode": "SETUP_LOW_MINUS_0_25_PRIOR_ATR",
            "target_mode": "NET_COST_ADJUSTED_FIXED_R",
            "minimum_net_reward_r": 3.0,
            "maximum_hold_bars": 25,
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
        "family_id": "VOLATILITY_BREAKOUT",
        "asset_scope": ["BTC-USD", "ETH-USD"],
        "regime_scope": ["VOLATILITY_EXPANSION"],
        "indicator_set": [
            "DONCHIAN_CHANNEL",
            "ATR",
            "VOLUME_RATIO",
            "CLOSE_LOCATION",
            "ADX",
        ],
        "economic_thesis": (
            "A completed channel breakout that later retests and causally holds "
            "its breakout level before renewed price confirmation may reduce "
            "fragile direct-entry dependence under adverse trading costs."
        ),
        "signal_contract_id": "kraken-ai-v2-r2-breakout-retest-signal-v1",
        "execution_contract_id": "kraken-ai-v2-r2-breakout-retest-execution-v1",
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": ROUND_1_HYPOTHESIS_ORDER[3],
        "source_feedback_sha256s": [ROUND_1_REPORT_SHA256],
        "regime_parameters": {
            "donchian_prior_high_period": 55,
            "atr_period": 14,
            "atr_baseline_bars": 60,
            "atr_to_prior_median_gte": 1.1,
            "adx_period": 14,
            "adx_gte": 20.0,
        },
        "signal_parameters": {
            "setup_close_above_prior_55_high_required": True,
            "setup_volume_ratio_gte": 1.25,
            "setup_close_location_gte": 0.7,
            "retest_window_bars": 5,
            "retest_low_to_breakout_level_atr_lte": 0.25,
            "retest_close_at_or_above_breakout_level_required": True,
            "confirmation_close_above_prior_high_required": True,
            "confirmation_volume_ratio_gte": 1.0,
        },
        "execution_parameters": {
            "maximum_upward_gap_atr": 0.5,
            "stop_mode": "RETEST_LOW_MINUS_0_25_PRIOR_ATR",
            "target_mode": "NET_COST_ADJUSTED_FIXED_R",
            "minimum_net_reward_r": 3.0,
            "maximum_hold_bars": 60,
            "scheduled_exit": (
                "COMPLETED_CLOSE_BELOW_PRIOR_10_CLOSE_LOW_NEXT_OPEN"
            ),
        },
        "direct_breakout_entry_reused": False,
        "minimum_net_reward_r": 3.0,
        "causal_completed_bar_only": True,
        "next_open_entry_required": True,
        "rolling_baselines_exclude_current_bar": True,
    },
    {
        "hypothesis_id": HYPOTHESIS_ORDER[2],
        "family_id": "TREND_PULLBACK_CONTINUATION",
        "asset_scope": ["BTC-USD", "ETH-USD"],
        "regime_scope": ["UPTREND_PULLBACK"],
        "indicator_set": ["EMA", "ADX", "MACD", "VOLUME_RATIO", "ATR"],
        "economic_thesis": (
            "A multi-bar low-volume pullback inside a positive causal trend may "
            "resume more reliably after MACD momentum resets and crosses positive "
            "with a completed price and volume confirmation."
        ),
        "signal_contract_id": "kraken-ai-v2-r2-trend-macd-resumption-signal-v1",
        "execution_contract_id": (
            "kraken-ai-v2-r2-trend-macd-resumption-execution-v1"
        ),
        "development_gate_id": DEVELOPMENT_GATE_ID,
        "parent_hypothesis_id": ROUND_1_HYPOTHESIS_ORDER[1],
        "source_feedback_sha256s": [ROUND_1_REPORT_SHA256],
        "regime_parameters": {
            "pullback_ema_period": 20,
            "trend_ema_period": 50,
            "slow_ema_period": 200,
            "trend_slope_lookback_bars": 20,
            "adx_period": 14,
            "adx_gte": 20.0,
        },
        "signal_parameters": {
            "pullback_min_age_bars": 2,
            "pullback_max_age_bars": 5,
            "pullback_low_to_ema20_atr_lte": 0.5,
            "pullback_close_above_ema50_required": True,
            "pullback_volume_ratio_lte": 1.0,
            "macd_histogram_nonpositive_seen_required": True,
            "confirmation_macd_histogram_cross_above_zero_required": True,
            "confirmation_close_above_prior_3_high_required": True,
            "confirmation_volume_ratio_gte": 1.0,
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
)

ROUND_2_HYPOTHESES = copy.deepcopy(_ROUND_2_HYPOTHESES)


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


ROUND_2_MANIFEST = {
    "schema_version": SCHEMA_VERSION,
    "protocol_id": PARENT_PROTOCOL_ID,
    "round_id": ROUND_ID,
    "partition": "DEVELOPMENT",
    "hypotheses": [
        _manifest_hypothesis(hypothesis) for hypothesis in _ROUND_2_HYPOTHESES
    ],
    "development_data_access_authorized": False,
    "calibration_authorized": False,
    "evaluation_authorized": False,
    "automatic_mutation_authorized": False,
    "automatic_ranking_authorized": False,
    "candidate_v2_authorized": False,
    "round_execution_authorized": False,
}
ROUND_2_MANIFEST_LOCK = validate_hypothesis_manifest(ROUND_2_MANIFEST)

ROUND_1_EXECUTED_HYPOTHESIS_COUNT = len(ROUND_1_HYPOTHESIS_ORDER)
CUMULATIVE_HYPOTHESIS_COUNT = (
    ROUND_1_EXECUTED_HYPOTHESIS_COUNT
    + ROUND_2_MANIFEST_LOCK.payload["hypothesis_count"]
)
if CUMULATIVE_HYPOTHESIS_COUNT > DISCOVERY_BUDGET[
    "max_total_hypotheses_under_protocol"
]:  # pragma: no cover - immutable import-time invariant
    raise RuntimeError("Round 2 exceeds the cumulative discovery budget.")


@dataclass(frozen=True)
class LockedRound2Configuration:
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
        raise ValueError("Round 2 configuration must be canonical JSON data.") from exc


def _reference_configuration():
    maximum_total = DISCOVERY_BUDGET["max_total_hypotheses_under_protocol"]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "protocol_id": PROTOCOL_ID,
        "parent_protocol_id": PARENT_PROTOCOL_ID,
        "round_1_protocol_id": ROUND_1_PROTOCOL_ID,
        "round_id": ROUND_ID,
        "partition": "DEVELOPMENT",
        "asset_order": list(ASSET_ORDER),
        "hypothesis_order": list(HYPOTHESIS_ORDER),
        "hypotheses": copy.deepcopy(_ROUND_2_HYPOTHESES),
        "manifest_sha256": ROUND_2_MANIFEST_LOCK.sha256,
        "round_1_closure_status": ROUND_1_CLOSURE_STATUS,
        "round_1_report_sha256": ROUND_1_REPORT_SHA256,
        "round_1_route_dispositions": copy.deepcopy(ROUND_1_ROUTE_DISPOSITIONS),
        "development_slices": [
            {"slice_id": item[0], "start_utc": item[1], "end_exclusive_utc": item[2]}
            for item in DEVELOPMENT_SLICES
        ],
        "cost_profiles": copy.deepcopy(COST_PROFILES),
        "shared_safety_envelope": copy.deepcopy(SHARED_SAFETY_ENVELOPE),
        "route_interest_gates": copy.deepcopy(ROUND_2_ROUTE_INTEREST_GATES),
        "selection_gates": copy.deepcopy(ROUND_2_SELECTION_GATES),
        "rounds_registered_under_protocol": 2,
        "maximum_rounds_under_protocol": DISCOVERY_BUDGET[
            "max_rounds_under_protocol"
        ],
        "round_1_executed_hypothesis_count": ROUND_1_EXECUTED_HYPOTHESIS_COUNT,
        "round_2_registered_hypothesis_count": ROUND_2_MANIFEST_LOCK.payload[
            "hypothesis_count"
        ],
        "cumulative_hypothesis_count": CUMULATIVE_HYPOTHESIS_COUNT,
        "maximum_total_hypotheses_under_protocol": maximum_total,
        "unused_hypothesis_capacity": maximum_total - CUMULATIVE_HYPOTHESIS_COUNT,
        "unused_capacity_is_execution_authorization": False,
        "future_round_registered": False,
        "future_round_authorized": False,
        "round_1_gates_weakened": False,
        "cost_profiles_changed": False,
        "development_slices_changed": False,
        "gap_and_partition_context_reset_required": True,
        "route_evaluation_unit": "ASSET_FAMILY_PAIR",
        "performance_comparison_policy": "ABSOLUTE_GATES_NO_LEADERBOARD",
        "same_asset_multiple_pass_policy": "SEPARATE_PORTFOLIO_REVIEW_REQUIRED",
    }


_REFERENCE_CONFIGURATION = _reference_configuration()


def lock_round_2_configuration(configuration=None):
    """Lock the exact pre-registered Round 2 configuration without data access."""

    candidate = copy.deepcopy(
        _REFERENCE_CONFIGURATION if configuration is None else configuration
    )
    if candidate != _REFERENCE_CONFIGURATION:
        raise ValueError("Round 2 configuration mismatch after pre-registration.")
    digest = hashlib.sha256(_canonical_json_bytes(candidate)).hexdigest()
    return LockedRound2Configuration(payload=candidate, sha256=digest)


ROUND_2_CONFIGURATION_LOCK = lock_round_2_configuration()


def round_2_declaration():
    """Return Round 2 registration and explicit nonauthorization."""

    declaration = copy.deepcopy(ROUND_2_CONFIGURATION_LOCK.payload)
    declaration.update(
        {
            "configuration_sha256": ROUND_2_CONFIGURATION_LOCK.sha256,
            "hypothesis_count": ROUND_2_MANIFEST_LOCK.payload["hypothesis_count"],
            "family_variant_counts": copy.deepcopy(
                ROUND_2_MANIFEST_LOCK.payload["family_variant_counts"]
            ),
            "asset_route_counts": copy.deepcopy(
                ROUND_2_MANIFEST_LOCK.payload["asset_route_counts"]
            ),
            "round_1_closed": True,
            "round_1_rerun_authorized": False,
            "round_2_manifest_registered": True,
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
            "automatic_ranking_generated": False,
            "automatic_ranking_authorized": False,
            "automatic_strategy_selection_authorized": False,
            "runtime_learning_authorized": False,
            "calibration_authorized": False,
            "evaluation_authorized": False,
            "candidate_v2_authorized": False,
            "bounded_forward_paper_authorized": False,
            "cloud_execution_authorized": False,
            "live_execution_authorized": False,
            "next_stage": "IMPLEMENT_ROUND_2_CAUSAL_COMPONENTS_SYNTHETIC_ONLY",
        }
    )
    return declaration

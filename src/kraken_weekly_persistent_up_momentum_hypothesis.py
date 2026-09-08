"""Frozen weekly persistent-UP momentum hypothesis; no data access or run."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json


SCHEMA_VERSION = 1
PROTOCOL_ID = "kraken-btc-eth-xrp-weekly-persistent-up-momentum-hypothesis-v1"
COMPONENT_ID = "kraken-weekly-persistent-up-momentum-hypothesis-v1"
PARENT_COMMIT = "a9307dfe46078b1509c777710238057a81f790b5"

DATASET_ID = "kraken-spot-btc-eth-xrp-native-1d-20190101-20260401-archive-only-v2"
DATASET_MANIFEST_SHA256 = (
    "8c91b42f2bc0c16a0ef0c6b4373572ac53fbf7f5937d4ebbbe75a0d39483df1c"
)
ROUND_2_CLOSURE_STATUS = "KRAKEN_AI_V2_ROUND_2_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH"
TERMINAL_12H_STATUS = (
    "KRAKEN_AI_V2_REGIME_GATED_SELECTIVE_NO_VIABLE_HYPOTHESIS_"
    "STOP_KRAKEN_12H_RESEARCH"
)
TERMINAL_12H_REPORT_SHA256 = (
    "a972088fca185266a4a726b3a4512a90bed15f4e1d3a3467e76bedd171a7f286"
)

ASSET_ORDER = ("BTC-USD", "ETH-USD", "XRP-USD")
SOURCE_RESOLUTION = "1d"
DECISION_RESOLUTION = "1w"
WEEK_START = "MONDAY_00_00_UTC"
WEEKLY_OBSERVATION_COUNT = 7
MOMENTUM_LOOKBACK_WEEKS = 4
FORWARD_HORIZON_WEEKS = 1
STATE_ORDER = ("UP", "DOWN", "INSUFFICIENT")
ACTION_ORDER = ("LONG", "HOLD_CASH")
OUTCOME_ORDER = ("NEXT_WEEK_NET_POSITIVE", "NEXT_WEEK_NET_NONPOSITIVE")

PRIMARY_RULE_ID = "PERSISTENT_UP_ASSET_MOMENTUM"
CONTROL_ORDER = (
    "CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL",
    "PERSISTENT_UP_MARKET_ONLY_CONTROL",
)

DEVELOPMENT_START = "2019-01-01T00:00:00Z"
DEVELOPMENT_END_EXCLUSIVE = "2024-04-01T00:00:00Z"
DEVELOPMENT_SLICES = (
    {
        "slice_id": "D1",
        "start_inclusive": "2019-02-04T00:00:00Z",
        "end_exclusive": "2020-01-06T00:00:00Z",
    },
    {
        "slice_id": "D2",
        "start_inclusive": "2020-01-06T00:00:00Z",
        "end_exclusive": "2021-01-04T00:00:00Z",
    },
    {
        "slice_id": "D3",
        "start_inclusive": "2021-01-04T00:00:00Z",
        "end_exclusive": "2022-01-03T00:00:00Z",
    },
    {
        "slice_id": "D4",
        "start_inclusive": "2022-01-03T00:00:00Z",
        "end_exclusive": "2023-01-02T00:00:00Z",
    },
    {
        "slice_id": "D5",
        "start_inclusive": "2023-01-02T00:00:00Z",
        "end_exclusive": "2024-04-01T00:00:00Z",
    },
)

COST_PROFILES = {
    "KRAKEN_BASELINE_ADVERSE": {
        "profile_id": "kraken-tier1-taker-adverse-20260829-v1",
        "commission_rate_each_side": 0.008,
        "slippage_rate_each_side": 0.0015,
        "full_spread_rate": 0.003,
    },
    "KRAKEN_STRESS_ADVERSE": {
        "profile_id": "kraken-tier1-taker-stress-20260829-v1",
        "commission_rate_each_side": 0.008,
        "slippage_rate_each_side": 0.003,
        "full_spread_rate": 0.006,
    },
}

DEVELOPMENT_GATES = {
    "minimum_valid_primary_events_per_asset": 30,
    "minimum_events_per_counted_slice": 4,
    "minimum_counted_slices": 4,
    "minimum_nonnegative_baseline_slices": 4,
    "minimum_nonnegative_stress_slices": 3,
    "overall_baseline_mean_net_return_strictly_positive": True,
    "overall_stress_mean_net_return_nonnegative": True,
    "maximum_largest_event_positive_profit_share": 0.40,
    "minimum_assets_passing_all_gates": 2,
    "primary_beats_both_controls_on_minimum_assets": 2,
}

LITERATURE_REFERENCES = (
    {
        "citation": "Liu and Tsyvinski, Risks and Returns of Cryptocurrency",
        "doi": "10.1093/rfs/hhaa113",
        "role": "HYPOTHESIS_RATIONALE_ONLY",
    },
    {
        "citation": (
            "Hsieh, Huang and Liu, State transitions and momentum effect in "
            "cryptocurrency market"
        ),
        "doi": "10.1016/j.frl.2025.108356",
        "role": "HYPOTHESIS_RATIONALE_ONLY",
    },
)

SAFETY_FLAGS = (
    "source_values_opened",
    "kraken_archive_opened",
    "real_weekly_aggregation_executed",
    "outcomes_generated",
    "model_training_authorized",
    "model_training_executed",
    "development_run_authorized",
    "development_run_executed",
    "parameter_search_authorized",
    "threshold_search_authorized",
    "automatic_asset_selection_authorized",
    "portfolio_allocation_executed",
    "calibration_data_opened",
    "evaluation_data_opened",
    "candidate_v2_authorized",
    "bounded_forward_paper_authorized",
    "cloud_execution_authorized",
    "real_orders_submitted",
    "live_execution_authorized",
)


def _canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _configuration():
    return {
        "novelty": {
            "prior_daily_rule_rounds_reopened": False,
            "prior_12h_learning_reopened": False,
            "source_resolution": SOURCE_RESOLUTION,
            "decision_resolution": DECISION_RESOLUTION,
            "decision_target": "FIXED_NEXT_WEEK_NET_RETURN",
            "static_indicator_regime_reused": False,
            "state_transition_required": "UP_TO_UP",
            "literature_informed_derivative_not_replication": True,
        },
        "weekly_boundary": {
            "timezone": "UTC",
            "week_start": WEEK_START,
            "interval": "[MONDAY_00_00_UTC,NEXT_MONDAY_00_00_UTC)",
            "required_native_daily_observations": WEEKLY_OBSERVATION_COUNT,
            "required_daily_frequency": "1d",
            "aggregation": {
                "Open": "FIRST_OBSERVED_OPEN",
                "High": "MAX_OBSERVED_HIGH",
                "Low": "MIN_OBSERVED_LOW",
                "Close": "LAST_OBSERVED_CLOSE",
                "Volume": "SUM_OBSERVED_VOLUME",
                "Trades": "SUM_OBSERVED_TRADES",
            },
            "incomplete_week_policy": "INVALID_NO_FILL",
            "provider_gap_policy": "INVALIDATE_WEEK_AND_RESET_LOOKBACK",
            "market_proxy_requires_all_assets_complete": True,
        },
        "causal_signal": {
            "observation_boundary": "AFTER_COMPLETED_WEEK_T",
            "momentum_lookback_weeks": MOMENTUM_LOOKBACK_WEEKS,
            "market_weekly_return": "EQUAL_WEIGHT_MEAN_OF_THREE_ASSET_WEEKLY_RETURNS",
            "market_four_week_return": "COMPOUNDED_COMPLETED_WEEKLY_RETURNS",
            "up_state_rule": "MARKET_FOUR_WEEK_RETURN_GREATER_THAN_OR_EQUAL_TO_ZERO",
            "persistent_up_rule": "STATE_T_MINUS_1_UP_AND_STATE_T_UP",
            "asset_four_week_return": "COMPOUNDED_COMPLETED_WEEKLY_RETURNS",
            "asset_momentum_rule": "ASSET_FOUR_WEEK_RETURN_STRICTLY_POSITIVE",
            "primary_rule_id": PRIMARY_RULE_ID,
            "eligible_action": "LONG",
            "fallback_action": "HOLD_CASH",
            "zero_market_return_state": "UP",
            "zero_asset_return_action": "HOLD_CASH",
            "future_information_permitted": False,
        },
        "outcome": {
            "entry_boundary": "FIRST_VALID_SOURCE_OPEN_OF_WEEK_T_PLUS_1",
            "exit_boundary": "FIRST_VALID_SOURCE_OPEN_OF_WEEK_T_PLUS_2",
            "forward_horizon_weeks": FORWARD_HORIZON_WEEKS,
            "direction": "LONG_ONLY",
            "outcome_order": list(OUTCOME_ORDER),
            "zero_net_return_class": "NEXT_WEEK_NET_NONPOSITIVE",
            "missing_boundary_policy": "INVALID_COUNTED_NO_SUBSTITUTION",
            "adverse_price_rate_formula": "SLIPPAGE_PLUS_HALF_FULL_SPREAD",
            "entry_fill_formula": "OPEN_T_PLUS_1_TIMES_ONE_PLUS_ADVERSE_PRICE_RATE",
            "exit_fill_formula": "OPEN_T_PLUS_2_TIMES_ONE_MINUS_ADVERSE_PRICE_RATE",
            "entry_cash_formula": "ENTRY_FILL_TIMES_ONE_PLUS_COMMISSION",
            "exit_proceeds_formula": "EXIT_FILL_TIMES_ONE_MINUS_COMMISSION",
            "net_return_formula": (
                "EXIT_PROCEEDS_MINUS_ENTRY_CASH_DIVIDED_BY_ENTRY_CASH"
            ),
            "event_identity": "ONE_VALID_ELIGIBLE_ASSET_WEEK",
            "consecutive_event_policy": "ADJACENT_NONOVERLAPPING_EVENTS_ALLOWED",
            "cost_profiles": deepcopy(COST_PROFILES),
            "protective_stop_implemented": False,
            "position_sizing_implemented": False,
            "portfolio_simulation_authorized": False,
            "signal_feasibility_only": True,
        },
        "controls": {
            "control_order": list(CONTROL_ORDER),
            "definitions": {
                "CURRENT_UP_ONLY_ASSET_MOMENTUM_CONTROL": (
                    "STATE_T_UP_AND_ASSET_FOUR_WEEK_RETURN_STRICTLY_POSITIVE"
                ),
                "PERSISTENT_UP_MARKET_ONLY_CONTROL": (
                    "STATE_T_MINUS_1_UP_AND_STATE_T_UP"
                ),
            },
            "shared_timing_outcome_and_cost_boundary": True,
            "candidate_eligible": False,
            "ranking_authorized": False,
            "purpose": "MECHANISM_ABLATION_ONLY",
        },
        "development": {
            "partition": "DEVELOPMENT",
            "start_inclusive": DEVELOPMENT_START,
            "end_exclusive": DEVELOPMENT_END_EXCLUSIVE,
            "slices": [dict(item) for item in DEVELOPMENT_SLICES],
            "model_family": "NONE_RULE_BASED_SIGNAL_BASELINE",
            "model_fit_count": 0,
            "single_future_execution_ceiling": 1,
            "gates": deepcopy(DEVELOPMENT_GATES),
            "failure_action": "HOLD_CASH_AND_CLOSE_EXACT_HYPOTHESIS",
            "threshold_rescue_authorized": False,
        },
        "literature": [dict(item) for item in LITERATURE_REFERENCES],
    }


def weekly_persistent_up_momentum_hypothesis_declaration():
    configuration = _configuration()
    declaration = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "dataset_id": DATASET_ID,
        "dataset_manifest_sha256": DATASET_MANIFEST_SHA256,
        "asset_order": list(ASSET_ORDER),
        "round_2_closure_status": ROUND_2_CLOSURE_STATUS,
        "terminal_12h_status": TERMINAL_12H_STATUS,
        "terminal_12h_report_sha256": TERMINAL_12H_REPORT_SHA256,
        "primary_rule_id": PRIMARY_RULE_ID,
        "control_order": list(CONTROL_ORDER),
        "action_order": list(ACTION_ORDER),
        "configuration": configuration,
        "configuration_sha256": hashlib.sha256(_canonical_json(configuration)).hexdigest(),
        "status": "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_HYPOTHESIS_FROZEN_NO_DATA_OR_RUN",
        "next_stage": "SEPARATE_SYNTHETIC_ONLY_IMPLEMENTATION_DECISION",
    }
    declaration.update({name: False for name in SAFETY_FLAGS})
    return declaration


def validate_weekly_persistent_up_momentum_hypothesis(candidate):
    if not isinstance(candidate, dict):
        raise TypeError("Weekly persistent-UP hypothesis must be a dictionary.")
    expected = weekly_persistent_up_momentum_hypothesis_declaration()
    unknown = set(candidate) - set(expected)
    missing = set(expected) - set(candidate)
    if unknown:
        raise ValueError(f"Unknown weekly hypothesis fields: {sorted(unknown)}.")
    if missing:
        raise ValueError(f"Missing weekly hypothesis fields: {sorted(missing)}.")
    if candidate != expected:
        raise ValueError("Weekly persistent-UP hypothesis differs from the frozen declaration.")
    if any(candidate[name] is not False for name in SAFETY_FLAGS):
        raise ValueError("Weekly persistent-UP hypothesis safety boundary is open.")
    return deepcopy(candidate)


def main():
    print(
        json.dumps(
            weekly_persistent_up_momentum_hypothesis_declaration(),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

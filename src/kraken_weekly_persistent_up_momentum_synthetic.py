"""Pure in-memory synthetic engine for the frozen weekly momentum hypothesis."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext

try:
    from kraken_weekly_persistent_up_momentum_hypothesis import (
        ASSET_ORDER,
        CONTROL_ORDER,
        COST_PROFILES,
        DEVELOPMENT_END_EXCLUSIVE,
        DEVELOPMENT_START,
        MOMENTUM_LOOKBACK_WEEKS,
        PRIMARY_RULE_ID,
        PROTOCOL_ID as HYPOTHESIS_PROTOCOL_ID,
    )
except ImportError:  # pragma: no cover - package import compatibility
    from .kraken_weekly_persistent_up_momentum_hypothesis import (
        ASSET_ORDER,
        CONTROL_ORDER,
        COST_PROFILES,
        DEVELOPMENT_END_EXCLUSIVE,
        DEVELOPMENT_START,
        MOMENTUM_LOOKBACK_WEEKS,
        PRIMARY_RULE_ID,
        PROTOCOL_ID as HYPOTHESIS_PROTOCOL_ID,
    )


SCHEMA_VERSION = 1
PROTOCOL_ID = (
    "kraken-btc-eth-xrp-weekly-persistent-up-momentum-"
    "synthetic-implementation-v1"
)
COMPONENT_ID = "kraken-weekly-persistent-up-momentum-synthetic-engine-v1"
PARENT_COMMIT = "f7ca20a77f203a4a732d79d5fda4812954a956b2"
SYNTHETIC_AUTHORIZATION_TOKEN = (
    "KRAKEN_WEEKLY_PERSISTENT_UP_SYNTHETIC_FIXTURE_V1"
)
INPUT_MODE = "SYNTHETIC_TEST_ONLY"
DAILY_FIELD_ORDER = (
    "timestamp",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "trades",
)
RULE_ORDER = (PRIMARY_RULE_ID, *CONTROL_ORDER)
COST_PROFILE_ORDER = ("KRAKEN_BASELINE_ADVERSE", "KRAKEN_STRESS_ADVERSE")

REAL_SAFETY_FLAGS = (
    "source_values_opened",
    "kraken_archive_opened",
    "real_weekly_aggregation_executed",
    "real_outcomes_generated",
    "model_training_authorized",
    "model_training_executed",
    "development_run_authorized",
    "development_run_executed",
    "parameter_search_authorized",
    "threshold_search_authorized",
    "calibration_data_opened",
    "evaluation_data_opened",
    "candidate_v2_authorized",
    "bounded_forward_paper_authorized",
    "cloud_execution_authorized",
    "real_orders_submitted",
    "live_execution_authorized",
)


def synthetic_implementation_declaration():
    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "hypothesis_protocol_id": HYPOTHESIS_PROTOCOL_ID,
        "input_mode": INPUT_MODE,
        "asset_order": list(ASSET_ORDER),
        "daily_field_order": list(DAILY_FIELD_ORDER),
        "rule_order": list(RULE_ORDER),
        "cost_profile_order": list(COST_PROFILE_ORDER),
        "synthetic_authorization_token": SYNTHETIC_AUTHORIZATION_TOKEN,
        "synthetic_engine_implemented": True,
        "synthetic_fixture_execution_permitted": True,
        "filesystem_reader_implemented": False,
        "network_reader_implemented": False,
        "development_gate_evaluator_implemented": False,
        "status": (
            "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_SYNTHETIC_ENGINE_"
            "FROZEN_NO_REAL_DATA_OR_RUN"
        ),
        "next_stage": "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_DESIGN_DECISION",
    }
    result.update({name: False for name in REAL_SAFETY_FLAGS})
    return result


def validate_synthetic_implementation_declaration(candidate):
    if not isinstance(candidate, dict):
        raise TypeError("Synthetic implementation declaration must be a dictionary.")
    expected = synthetic_implementation_declaration()
    if set(candidate) - set(expected):
        raise ValueError("Synthetic implementation declaration has unknown fields.")
    if set(expected) - set(candidate):
        raise ValueError("Synthetic implementation declaration has missing fields.")
    if candidate != expected:
        raise ValueError("Synthetic implementation differs from the frozen declaration.")
    if any(candidate[name] is not False for name in REAL_SAFETY_FLAGS):
        raise ValueError("Synthetic implementation real-data safety boundary is open.")
    return deepcopy(candidate)


def _require_synthetic_authorization(token):
    if token != SYNTHETIC_AUTHORIZATION_TOKEN:
        raise PermissionError("Explicit synthetic fixture authorization is required.")


def _parse_utc_midnight(value, label):
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a canonical UTC timestamp string.")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError as exc:
        raise ValueError(f"{label} must be canonical UTC midnight.") from exc
    if parsed.hour or parsed.minute or parsed.second or parsed.microsecond:
        raise ValueError(f"{label} must be UTC midnight.")
    return parsed


def _iso(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _decimal(value, label):
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric, not boolean.")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be numeric.") from exc
    if not number.is_finite():
        raise ValueError(f"{label} must be finite.")
    return number


def _decimal_text(value):
    if value == 0:
        return "0"
    rendered = format(value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered


def _validated_daily_rows(daily_rows_by_asset):
    if not isinstance(daily_rows_by_asset, dict):
        raise TypeError("Synthetic daily rows must be an exact asset dictionary.")
    if set(daily_rows_by_asset) != set(ASSET_ORDER):
        raise ValueError("Synthetic daily rows must contain exactly the frozen assets.")

    start = _parse_utc_midnight(DEVELOPMENT_START, "Development start")
    end = _parse_utc_midnight(DEVELOPMENT_END_EXCLUSIVE, "Development end")
    validated = {}
    for asset in ASSET_ORDER:
        source_rows = daily_rows_by_asset[asset]
        if not isinstance(source_rows, (list, tuple)) or not source_rows:
            raise ValueError(f"{asset} synthetic rows must be a nonempty list or tuple.")
        asset_rows = []
        previous_timestamp = None
        for index, source_row in enumerate(source_rows):
            label = f"{asset} row {index}"
            if not isinstance(source_row, dict):
                raise TypeError(f"{label} must be a dictionary.")
            if set(source_row) != set(DAILY_FIELD_ORDER):
                raise ValueError(f"{label} must contain exactly the frozen daily fields.")
            timestamp = _parse_utc_midnight(source_row["timestamp"], "timestamp")
            if not start <= timestamp < end:
                raise ValueError(f"{label} is outside the Development partition.")
            if previous_timestamp is not None and timestamp <= previous_timestamp:
                raise ValueError(f"{asset} timestamps must be strictly increasing.")
            previous_timestamp = timestamp

            open_ = _decimal(source_row["open"], f"{label} open")
            high = _decimal(source_row["high"], f"{label} high")
            low = _decimal(source_row["low"], f"{label} low")
            close = _decimal(source_row["close"], f"{label} close")
            volume = _decimal(source_row["volume"], f"{label} volume")
            trades_value = _decimal(source_row["trades"], f"{label} trades")
            if min(open_, high, low, close) <= 0:
                raise ValueError(f"{label} OHLC values must be positive.")
            if high < max(open_, close) or low > min(open_, close) or high < low:
                raise ValueError(f"{label} OHLC geometry is invalid.")
            if volume < 0:
                raise ValueError(f"{label} volume must be nonnegative.")
            if trades_value <= 0 or trades_value != trades_value.to_integral_value():
                raise ValueError(f"{label} trades must be a positive integer.")
            asset_rows.append(
                {
                    "timestamp": timestamp,
                    "open": open_,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "trades": int(trades_value),
                }
            )
        validated[asset] = asset_rows
    return validated


def _monday(value):
    return value - timedelta(days=value.weekday())


def _week_starts(validated):
    first = min(_monday(rows[0]["timestamp"]) for rows in validated.values())
    last = max(_monday(rows[-1]["timestamp"]) for rows in validated.values())
    count = ((last - first).days // 7) + 1
    return tuple(first + timedelta(days=7 * index) for index in range(count))


def _aggregate_internal(validated):
    week_starts = _week_starts(validated)
    weekly_maps = {asset: {} for asset in ASSET_ORDER}
    public_valid = {asset: [] for asset in ASSET_ORDER}
    public_invalid = {asset: [] for asset in ASSET_ORDER}

    for asset in ASSET_ORDER:
        rows_by_timestamp = {row["timestamp"]: row for row in validated[asset]}
        for week_start in week_starts:
            expected = tuple(
                week_start + timedelta(days=offset) for offset in range(7)
            )
            observed = [
                rows_by_timestamp[value]
                for value in expected
                if value in rows_by_timestamp
            ]
            missing = [value for value in expected if value not in rows_by_timestamp]
            if missing:
                weekly_maps[asset][week_start] = None
                public_invalid[asset].append(
                    {
                        "asset": asset,
                        "week_start": _iso(week_start),
                        "week_end_exclusive": _iso(week_start + timedelta(days=7)),
                        "observed_daily_count": len(observed),
                        "missing_daily_timestamps": [_iso(value) for value in missing],
                        "reason": "INCOMPLETE_WEEK_NO_FILL",
                    }
                )
                continue
            weekly = {
                "asset": asset,
                "week_start": week_start,
                "week_end_exclusive": week_start + timedelta(days=7),
                "open": observed[0]["open"],
                "high": max(row["high"] for row in observed),
                "low": min(row["low"] for row in observed),
                "close": observed[-1]["close"],
                "volume": sum((row["volume"] for row in observed), Decimal(0)),
                "trades": sum(row["trades"] for row in observed),
            }
            weekly_maps[asset][week_start] = weekly
            public_valid[asset].append(_public_weekly_bar(weekly))

    public = {
        "status": "SYNTHETIC_COMPLETE_WEEK_AGGREGATION_PASS",
        "input_mode": INPUT_MODE,
        "week_start_order": [_iso(value) for value in week_starts],
        "daily_input_count_by_asset": {
            asset: len(validated[asset]) for asset in ASSET_ORDER
        },
        "valid_week_count_by_asset": {
            asset: len(public_valid[asset]) for asset in ASSET_ORDER
        },
        "invalid_week_count_by_asset": {
            asset: len(public_invalid[asset]) for asset in ASSET_ORDER
        },
        "valid_weeks_by_asset": public_valid,
        "invalid_weeks_by_asset": public_invalid,
        "fill_or_interpolation_used": False,
    }
    return week_starts, weekly_maps, public


def _public_weekly_bar(weekly):
    return {
        "asset": weekly["asset"],
        "week_start": _iso(weekly["week_start"]),
        "week_end_exclusive": _iso(weekly["week_end_exclusive"]),
        "open": _decimal_text(weekly["open"]),
        "high": _decimal_text(weekly["high"]),
        "low": _decimal_text(weekly["low"]),
        "close": _decimal_text(weekly["close"]),
        "volume": _decimal_text(weekly["volume"]),
        "trades": weekly["trades"],
        "source_observation_count": 7,
    }


def aggregate_synthetic_daily_rows(
    daily_rows_by_asset, *, authorization_token
):
    _require_synthetic_authorization(authorization_token)
    validated = _validated_daily_rows(daily_rows_by_asset)
    _, _, public = _aggregate_internal(validated)
    public.update({name: False for name in REAL_SAFETY_FLAGS})
    public["synthetic_pipeline_executed"] = True
    return public


def _asset_momentum(segment, weekly_maps, asset):
    with localcontext() as context:
        context.prec = 50
        first = weekly_maps[asset][segment[-5]]["close"]
        last = weekly_maps[asset][segment[-1]]["close"]
        return (last / first) - Decimal(1)


def _market_four_week_return(segment, weekly_maps):
    with localcontext() as context:
        context.prec = 50
        growth = Decimal(1)
        for previous_week, current_week in zip(segment[-5:-1], segment[-4:]):
            asset_returns = []
            for asset in ASSET_ORDER:
                previous_close = weekly_maps[asset][previous_week]["close"]
                current_close = weekly_maps[asset][current_week]["close"]
                asset_returns.append((current_close / previous_close) - Decimal(1))
            market_return = sum(asset_returns, Decimal(0)) / Decimal(len(ASSET_ORDER))
            growth *= Decimal(1) + market_return
        return growth - Decimal(1)


def _state(value):
    if value is None:
        return "INSUFFICIENT"
    return "UP" if value >= 0 else "DOWN"


def _hold(reason):
    return {"action": "HOLD_CASH", "eligibility_reason": reason}


def _long():
    return {"action": "LONG", "eligibility_reason": "ELIGIBLE"}


def _rule_actions(market_complete, current_state, previous_state, momentum):
    if not market_complete:
        return {rule: _hold("MARKET_WEEK_INCOMPLETE") for rule in RULE_ORDER}

    if current_state == "INSUFFICIENT":
        return {rule: _hold("CURRENT_MARKET_STATE_INSUFFICIENT") for rule in RULE_ORDER}

    if current_state != "UP":
        return {rule: _hold("CURRENT_MARKET_STATE_NOT_UP") for rule in RULE_ORDER}

    if momentum is None:
        current_control = _hold("ASSET_MOMENTUM_INSUFFICIENT")
    elif momentum > 0:
        current_control = _long()
    else:
        current_control = _hold("ASSET_MOMENTUM_NOT_POSITIVE")

    if previous_state == "INSUFFICIENT":
        persistent_market = _hold("PRIOR_MARKET_STATE_INSUFFICIENT")
    elif previous_state != "UP":
        persistent_market = _hold("PRIOR_MARKET_STATE_NOT_UP")
    else:
        persistent_market = _long()

    if persistent_market["action"] != "LONG":
        primary = dict(persistent_market)
    elif momentum is None:
        primary = _hold("ASSET_MOMENTUM_INSUFFICIENT")
    elif momentum <= 0:
        primary = _hold("ASSET_MOMENTUM_NOT_POSITIVE")
    else:
        primary = _long()

    return {
        PRIMARY_RULE_ID: primary,
        CONTROL_ORDER[0]: current_control,
        CONTROL_ORDER[1]: persistent_market,
    }


def _cost_result(entry_open, exit_open, profile):
    with localcontext() as context:
        context.prec = 50
        commission = Decimal(str(profile["commission_rate_each_side"]))
        slippage = Decimal(str(profile["slippage_rate_each_side"]))
        spread = Decimal(str(profile["full_spread_rate"]))
        adverse = slippage + (spread / Decimal(2))
        entry_fill = entry_open * (Decimal(1) + adverse)
        exit_fill = exit_open * (Decimal(1) - adverse)
        entry_cash = entry_fill * (Decimal(1) + commission)
        exit_proceeds = exit_fill * (Decimal(1) - commission)
        net_return = (exit_proceeds - entry_cash) / entry_cash
    return {
        "profile_id": profile["profile_id"],
        "adverse_price_rate_each_side": _decimal_text(adverse),
        "entry_fill": _decimal_text(entry_fill),
        "exit_fill": _decimal_text(exit_fill),
        "entry_cash": _decimal_text(entry_cash),
        "exit_proceeds": _decimal_text(exit_proceeds),
        "net_return": _decimal_text(net_return),
        "outcome_class": (
            "NEXT_WEEK_NET_POSITIVE"
            if net_return > 0
            else "NEXT_WEEK_NET_NONPOSITIVE"
        ),
    }


def _synthetic_outcome(asset, decision_week, weekly_maps):
    entry_week = decision_week + timedelta(days=7)
    exit_week = decision_week + timedelta(days=14)
    missing = []
    if weekly_maps[asset].get(entry_week) is None:
        missing.append("ENTRY_WEEK_T_PLUS_1")
    if weekly_maps[asset].get(exit_week) is None:
        missing.append("EXIT_WEEK_T_PLUS_2")
    if missing:
        return {
            "status": "INVALID_MISSING_FUTURE_BOUNDARY",
            "entry_week_start": _iso(entry_week),
            "exit_week_start": _iso(exit_week),
            "missing_boundaries": missing,
        }

    entry_open = weekly_maps[asset][entry_week]["open"]
    exit_open = weekly_maps[asset][exit_week]["open"]
    return {
        "status": "VALID_SYNTHETIC_OUTCOME",
        "entry_week_start": _iso(entry_week),
        "exit_week_start": _iso(exit_week),
        "entry_reference_open": _decimal_text(entry_open),
        "exit_reference_open": _decimal_text(exit_open),
        "cost_profiles": {
            profile_name: _cost_result(
                entry_open, exit_open, COST_PROFILES[profile_name]
            )
            for profile_name in COST_PROFILE_ORDER
        },
    }


def evaluate_synthetic_weekly_fixture(
    daily_rows_by_asset, *, authorization_token
):
    _require_synthetic_authorization(authorization_token)
    validated = _validated_daily_rows(daily_rows_by_asset)
    week_starts, weekly_maps, aggregation = _aggregate_internal(validated)

    decisions = []
    segment = []
    valid_outcomes = {rule: 0 for rule in RULE_ORDER}
    invalid_outcomes = {rule: 0 for rule in RULE_ORDER}
    long_decisions = {rule: 0 for rule in RULE_ORDER}

    for week_start in week_starts:
        market_complete = all(
            weekly_maps[asset][week_start] is not None for asset in ASSET_ORDER
        )
        if market_complete:
            segment.append(week_start)
        else:
            segment = []

        current_market_return = None
        previous_market_return = None
        if len(segment) >= MOMENTUM_LOOKBACK_WEEKS + 1:
            current_market_return = _market_four_week_return(segment, weekly_maps)
        if len(segment) >= MOMENTUM_LOOKBACK_WEEKS + 2:
            previous_market_return = _market_four_week_return(
                segment[:-1], weekly_maps
            )
        current_state = _state(current_market_return)
        previous_state = _state(previous_market_return)

        for asset in ASSET_ORDER:
            momentum = None
            if len(segment) >= MOMENTUM_LOOKBACK_WEEKS + 1:
                momentum = _asset_momentum(segment, weekly_maps, asset)
            actions = _rule_actions(
                market_complete, current_state, previous_state, momentum
            )
            for rule in RULE_ORDER:
                if actions[rule]["action"] == "LONG":
                    long_decisions[rule] += 1
                    outcome = _synthetic_outcome(asset, week_start, weekly_maps)
                    if outcome["status"] == "VALID_SYNTHETIC_OUTCOME":
                        valid_outcomes[rule] += 1
                    else:
                        invalid_outcomes[rule] += 1
                else:
                    outcome = {"status": "NOT_APPLICABLE_HOLD_CASH"}
                actions[rule]["outcome"] = outcome

            decisions.append(
                {
                    "asset": asset,
                    "decision_week_start": _iso(week_start),
                    "market_week_complete": market_complete,
                    "asset_week_complete": (
                        weekly_maps[asset][week_start] is not None
                    ),
                    "consecutive_complete_market_weeks": len(segment),
                    "market_four_week_return": (
                        None
                        if current_market_return is None
                        else _decimal_text(current_market_return)
                    ),
                    "previous_market_four_week_return": (
                        None
                        if previous_market_return is None
                        else _decimal_text(previous_market_return)
                    ),
                    "market_state_current": current_state,
                    "market_state_previous": previous_state,
                    "asset_four_week_momentum": (
                        None if momentum is None else _decimal_text(momentum)
                    ),
                    "rule_actions": actions,
                }
            )

    result = {
        "schema_version": SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "component_id": COMPONENT_ID,
        "parent_commit": PARENT_COMMIT,
        "hypothesis_protocol_id": HYPOTHESIS_PROTOCOL_ID,
        "input_mode": INPUT_MODE,
        "asset_order": list(ASSET_ORDER),
        "rule_order": list(RULE_ORDER),
        "aggregation": aggregation,
        "decisions": decisions,
        "decision_count": len(decisions),
        "long_decision_count_by_rule": long_decisions,
        "valid_synthetic_outcome_count_by_rule": valid_outcomes,
        "invalid_synthetic_outcome_count_by_rule": invalid_outcomes,
        "synthetic_pipeline_executed": True,
        "synthetic_outcomes_generated": sum(valid_outcomes.values()) > 0,
        "development_gate_evaluation_executed": False,
        "status": "KRAKEN_WEEKLY_PERSISTENT_UP_MOMENTUM_SYNTHETIC_ENGINE_PASS",
        "next_stage": "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_DESIGN_DECISION",
    }
    result.update({name: False for name in REAL_SAFETY_FLAGS})
    return result

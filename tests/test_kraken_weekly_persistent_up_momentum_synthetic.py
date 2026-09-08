import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, localcontext
import os
import sys

import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_weekly_persistent_up_momentum_hypothesis import (
    ASSET_ORDER,
    CONTROL_ORDER,
    PRIMARY_RULE_ID,
)
from kraken_weekly_persistent_up_momentum_synthetic import (
    COMPONENT_ID,
    COST_PROFILE_ORDER,
    DAILY_FIELD_ORDER,
    INPUT_MODE,
    PARENT_COMMIT,
    PROTOCOL_ID,
    REAL_SAFETY_FLAGS,
    RULE_ORDER,
    SYNTHETIC_AUTHORIZATION_TOKEN,
    aggregate_synthetic_daily_rows,
    evaluate_synthetic_weekly_fixture,
    synthetic_implementation_declaration,
    validate_synthetic_implementation_declaration,
)


START = datetime(2020, 1, 6, tzinfo=timezone.utc)


def _iso(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _default_values(week_count):
    return [Decimal("100") * (Decimal("1.10") ** index) for index in range(week_count)]


def _fixture(
    week_count=8,
    *,
    closes_by_asset=None,
    opens_by_asset=None,
    missing=(),
):
    default_closes = _default_values(week_count)
    closes_by_asset = closes_by_asset or {
        asset: list(default_closes) for asset in ASSET_ORDER
    }
    opens_by_asset = opens_by_asset or {
        asset: list(closes_by_asset[asset]) for asset in ASSET_ORDER
    }
    missing = set(missing)
    result = {}
    for asset in ASSET_ORDER:
        rows = []
        for week_index in range(week_count):
            week_open = Decimal(str(opens_by_asset[asset][week_index]))
            week_close = Decimal(str(closes_by_asset[asset][week_index]))
            for day_index in range(7):
                if (asset, week_index, day_index) in missing:
                    continue
                timestamp = START + timedelta(days=(week_index * 7) + day_index)
                close = week_close if day_index == 6 else week_open
                high = max(week_open, close) + Decimal(1)
                low = min(week_open, close) - Decimal(1)
                rows.append(
                    {
                        "timestamp": _iso(timestamp),
                        "open": str(week_open),
                        "high": str(high),
                        "low": str(low),
                        "close": str(close),
                        "volume": str(Decimal(10 + day_index)),
                        "trades": day_index + 1,
                    }
                )
        result[asset] = rows
    return result


def _run(fixture):
    return evaluate_synthetic_weekly_fixture(
        fixture,
        authorization_token=SYNTHETIC_AUTHORIZATION_TOKEN,
    )


def _decision(result, asset, week_index):
    target = _iso(START + timedelta(days=7 * week_index))
    return next(
        item
        for item in result["decisions"]
        if item["asset"] == asset and item["decision_week_start"] == target
    )


def test_declaration_freezes_synthetic_only_identity_and_safety():
    declaration = synthetic_implementation_declaration()

    assert declaration["protocol_id"] == PROTOCOL_ID
    assert declaration["component_id"] == COMPONENT_ID
    assert declaration["parent_commit"] == PARENT_COMMIT
    assert declaration["parent_commit"].startswith("f7ca20a")
    assert declaration["input_mode"] == INPUT_MODE
    assert declaration["asset_order"] == list(ASSET_ORDER)
    assert declaration["daily_field_order"] == list(DAILY_FIELD_ORDER)
    assert declaration["rule_order"] == list(RULE_ORDER)
    assert declaration["cost_profile_order"] == list(COST_PROFILE_ORDER)
    assert declaration["synthetic_engine_implemented"] is True
    assert declaration["filesystem_reader_implemented"] is False
    assert declaration["network_reader_implemented"] is False
    assert declaration["development_gate_evaluator_implemented"] is False
    assert all(declaration[name] is False for name in REAL_SAFETY_FLAGS)


def test_declaration_validator_rejects_changes_and_returns_an_independent_copy():
    declaration = synthetic_implementation_declaration()
    validated = validate_synthetic_implementation_declaration(declaration)

    assert validated == declaration
    validated["source_values_opened"] = True
    assert synthetic_implementation_declaration()["source_values_opened"] is False

    changed = synthetic_implementation_declaration()
    changed["source_values_opened"] = True
    with pytest.raises(ValueError, match="differs|safety"):
        validate_synthetic_implementation_declaration(changed)


def test_declaration_validator_rejects_unknown_missing_and_nonmapping_values():
    unknown = synthetic_implementation_declaration()
    unknown["unknown"] = True
    with pytest.raises(ValueError, match="unknown"):
        validate_synthetic_implementation_declaration(unknown)

    missing = synthetic_implementation_declaration()
    del missing["status"]
    with pytest.raises(ValueError, match="missing"):
        validate_synthetic_implementation_declaration(missing)

    with pytest.raises(TypeError, match="dictionary"):
        validate_synthetic_implementation_declaration([])


def test_explicit_synthetic_token_and_exact_assets_are_required():
    fixture = _fixture(1)
    with pytest.raises(PermissionError, match="synthetic"):
        aggregate_synthetic_daily_rows(fixture, authorization_token="WRONG")

    del fixture["XRP-USD"]
    with pytest.raises(ValueError, match="exactly the frozen assets"):
        aggregate_synthetic_daily_rows(
            fixture,
            authorization_token=SYNTHETIC_AUTHORIZATION_TOKEN,
        )


def test_daily_rows_require_exact_schema_chronology_and_development_boundary():
    fixture = _fixture(1)
    fixture["BTC-USD"][0]["unknown"] = 1
    with pytest.raises(ValueError, match="exactly the frozen daily fields"):
        _run(fixture)

    fixture = _fixture(1)
    fixture["BTC-USD"][0], fixture["BTC-USD"][1] = (
        fixture["BTC-USD"][1],
        fixture["BTC-USD"][0],
    )
    with pytest.raises(ValueError, match="strictly increasing"):
        _run(fixture)

    fixture = _fixture(1)
    fixture["BTC-USD"][0]["timestamp"] = "2024-04-01T00:00:00Z"
    with pytest.raises(ValueError, match="outside the Development"):
        _run(fixture)

    fixture = _fixture(1)
    fixture["BTC-USD"][0]["timestamp"] = "2020-01-06T00:00:00+00:00"
    with pytest.raises(ValueError, match="canonical UTC midnight"):
        _run(fixture)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("open", "NaN", "finite"),
        ("low", "0", "positive"),
        ("high", "1", "geometry"),
        ("volume", "-1", "nonnegative"),
        ("trades", "1.5", "positive integer"),
        ("trades", True, "not boolean"),
    ),
)
def test_invalid_numeric_daily_values_fail_closed(field, value, message):
    fixture = _fixture(1)
    fixture["BTC-USD"][0][field] = value
    with pytest.raises((TypeError, ValueError), match=message):
        _run(fixture)


def test_complete_week_aggregates_exact_ohlcvt_without_mutating_input():
    fixture = _fixture(1)
    before = copy.deepcopy(fixture)

    aggregation = aggregate_synthetic_daily_rows(
        fixture,
        authorization_token=SYNTHETIC_AUTHORIZATION_TOKEN,
    )

    assert fixture == before
    btc = aggregation["valid_weeks_by_asset"]["BTC-USD"][0]
    assert btc == {
        "asset": "BTC-USD",
        "week_start": "2020-01-06T00:00:00Z",
        "week_end_exclusive": "2020-01-13T00:00:00Z",
        "open": "100",
        "high": "101",
        "low": "99",
        "close": "100",
        "volume": "91",
        "trades": 28,
        "source_observation_count": 7,
    }
    assert aggregation["fill_or_interpolation_used"] is False
    assert all(aggregation[name] is False for name in REAL_SAFETY_FLAGS)


def test_incomplete_week_is_recorded_without_fill_and_closes_all_rules():
    fixture = _fixture(1, missing={("XRP-USD", 0, 3)})
    result = _run(fixture)

    invalid = result["aggregation"]["invalid_weeks_by_asset"]["XRP-USD"][0]
    assert invalid["observed_daily_count"] == 6
    assert invalid["missing_daily_timestamps"] == ["2020-01-09T00:00:00Z"]
    assert invalid["reason"] == "INCOMPLETE_WEEK_NO_FILL"
    for asset in ASSET_ORDER:
        decision = _decision(result, asset, 0)
        assert decision["market_week_complete"] is False
        assert all(
            value["action"] == "HOLD_CASH"
            for value in decision["rule_actions"].values()
        )


def test_fully_absent_middle_week_is_enumerated_and_resets_the_segment():
    missing = {
        (asset, 1, day_index)
        for asset in ASSET_ORDER
        for day_index in range(7)
    }
    result = _run(_fixture(3, missing=missing))

    for asset in ASSET_ORDER:
        invalid = result["aggregation"]["invalid_weeks_by_asset"][asset][0]
        assert invalid["week_start"] == "2020-01-13T00:00:00Z"
        assert invalid["observed_daily_count"] == 0
        assert len(invalid["missing_daily_timestamps"]) == 7
        after_gap = _decision(result, asset, 2)
        assert after_gap["consecutive_complete_market_weeks"] == 1


def test_fifth_week_allows_only_current_up_control_and_sixth_allows_primary():
    result = _run(_fixture(8))

    fifth = _decision(result, "BTC-USD", 4)
    assert fifth["market_state_current"] == "UP"
    assert fifth["market_state_previous"] == "INSUFFICIENT"
    assert fifth["rule_actions"][PRIMARY_RULE_ID]["action"] == "HOLD_CASH"
    assert fifth["rule_actions"][CONTROL_ORDER[0]]["action"] == "LONG"
    assert fifth["rule_actions"][CONTROL_ORDER[1]]["action"] == "HOLD_CASH"

    sixth = _decision(result, "BTC-USD", 5)
    assert sixth["market_state_current"] == "UP"
    assert sixth["market_state_previous"] == "UP"
    assert all(
        sixth["rule_actions"][rule]["action"] == "LONG" for rule in RULE_ORDER
    )


def test_zero_market_return_is_up_but_zero_asset_momentum_is_not_eligible():
    flat = [Decimal("100")] * 8
    closes = {asset: list(flat) for asset in ASSET_ORDER}
    result = _run(_fixture(8, closes_by_asset=closes))
    btc = _decision(result, "BTC-USD", 5)

    assert btc["market_state_current"] == "UP"
    assert btc["market_state_previous"] == "UP"
    assert btc["market_four_week_return"] == "0"
    assert btc["asset_four_week_momentum"] == "0"
    assert btc["rule_actions"][PRIMARY_RULE_ID]["action"] == "HOLD_CASH"
    assert btc["rule_actions"][CONTROL_ORDER[0]]["action"] == "HOLD_CASH"
    assert btc["rule_actions"][CONTROL_ORDER[1]]["action"] == "LONG"


def test_market_only_control_can_long_when_asset_momentum_is_negative():
    falling = [
        Decimal("100") * (Decimal("0.90") ** index) for index in range(8)
    ]
    rising = [
        Decimal("100") * (Decimal("1.20") ** index) for index in range(8)
    ]
    closes = {
        "BTC-USD": falling,
        "ETH-USD": rising,
        "XRP-USD": rising,
    }
    btc = _decision(_run(_fixture(8, closes_by_asset=closes)), "BTC-USD", 5)

    assert btc["market_state_current"] == "UP"
    assert btc["market_state_previous"] == "UP"
    assert Decimal(btc["asset_four_week_momentum"]) < 0
    assert btc["rule_actions"][PRIMARY_RULE_ID]["action"] == "HOLD_CASH"
    assert btc["rule_actions"][CONTROL_ORDER[0]]["action"] == "HOLD_CASH"
    assert btc["rule_actions"][CONTROL_ORDER[1]]["action"] == "LONG"


def test_persistent_down_market_closes_every_rule():
    falling = [
        Decimal("100") * (Decimal("0.90") ** index) for index in range(8)
    ]
    closes = {asset: list(falling) for asset in ASSET_ORDER}
    decision = _decision(_run(_fixture(8, closes_by_asset=closes)), "ETH-USD", 5)

    assert decision["market_state_current"] == "DOWN"
    assert decision["market_state_previous"] == "DOWN"
    assert all(
        decision["rule_actions"][rule]["action"] == "HOLD_CASH"
        for rule in RULE_ORDER
    )


def test_gap_resets_state_and_momentum_before_six_new_complete_weeks():
    fixture = _fixture(12, missing={("XRP-USD", 5, 3)})
    result = _run(fixture)

    gap = _decision(result, "BTC-USD", 5)
    fifth_after_gap = _decision(result, "BTC-USD", 10)
    sixth_after_gap = _decision(result, "BTC-USD", 11)
    assert gap["consecutive_complete_market_weeks"] == 0
    assert fifth_after_gap["consecutive_complete_market_weeks"] == 5
    assert fifth_after_gap["rule_actions"][PRIMARY_RULE_ID]["action"] == "HOLD_CASH"
    assert sixth_after_gap["consecutive_complete_market_weeks"] == 6
    assert sixth_after_gap["rule_actions"][PRIMARY_RULE_ID]["action"] == "LONG"


def test_future_opens_change_outcome_but_not_signal_at_decision_week():
    original = _fixture(8)
    changed = copy.deepcopy(original)
    for asset in ASSET_ORDER:
        for week_index, multiplier in ((6, Decimal("0.5")), (7, Decimal("2"))):
            for day_index in range(7):
                row = changed[asset][(week_index * 7) + day_index]
                if day_index == 0:
                    new_open = Decimal(row["open"]) * multiplier
                    row["open"] = str(new_open)
                    row["high"] = str(max(new_open, Decimal(row["close"])) + 1)
                    row["low"] = str(min(new_open, Decimal(row["close"])) - 1)

    original_decision = _decision(_run(original), "BTC-USD", 5)
    changed_decision = _decision(_run(changed), "BTC-USD", 5)
    assert original_decision["market_state_current"] == changed_decision[
        "market_state_current"
    ]
    assert original_decision["asset_four_week_momentum"] == changed_decision[
        "asset_four_week_momentum"
    ]
    assert original_decision["rule_actions"][PRIMARY_RULE_ID]["action"] == (
        changed_decision["rule_actions"][PRIMARY_RULE_ID]["action"]
    )
    assert original_decision["rule_actions"][PRIMARY_RULE_ID]["outcome"] != (
        changed_decision["rule_actions"][PRIMARY_RULE_ID]["outcome"]
    )


def test_cost_math_is_exact_and_stress_is_more_adverse():
    result = _run(_fixture(8))
    outcome = _decision(result, "BTC-USD", 5)["rule_actions"][PRIMARY_RULE_ID][
        "outcome"
    ]
    baseline = outcome["cost_profiles"]["KRAKEN_BASELINE_ADVERSE"]
    stress = outcome["cost_profiles"]["KRAKEN_STRESS_ADVERSE"]

    with localcontext() as context:
        context.prec = 50
        entry = Decimal(outcome["entry_reference_open"])
        exit_ = Decimal(outcome["exit_reference_open"])
        expected_entry_cash = entry * Decimal("1.003") * Decimal("1.008")
        expected_exit_proceeds = exit_ * Decimal("0.997") * Decimal("0.992")
        expected_net = (
            expected_exit_proceeds - expected_entry_cash
        ) / expected_entry_cash

    assert Decimal(baseline["entry_cash"]) == expected_entry_cash
    assert Decimal(baseline["exit_proceeds"]) == expected_exit_proceeds
    assert Decimal(baseline["net_return"]) == expected_net
    assert baseline["outcome_class"] == "NEXT_WEEK_NET_POSITIVE"
    assert Decimal(stress["net_return"]) < Decimal(baseline["net_return"])


def test_flat_future_open_is_nonpositive_after_costs():
    closes = {asset: _default_values(8) for asset in ASSET_ORDER}
    opens = {asset: list(values) for asset, values in closes.items()}
    for asset in ASSET_ORDER:
        opens[asset][6] = Decimal("200")
        opens[asset][7] = Decimal("200")
    result = _run(_fixture(8, closes_by_asset=closes, opens_by_asset=opens))
    outcome = _decision(result, "BTC-USD", 5)["rule_actions"][PRIMARY_RULE_ID][
        "outcome"
    ]

    assert outcome["cost_profiles"]["KRAKEN_BASELINE_ADVERSE"][
        "outcome_class"
    ] == "NEXT_WEEK_NET_NONPOSITIVE"
    assert Decimal(
        outcome["cost_profiles"]["KRAKEN_BASELINE_ADVERSE"]["net_return"]
    ) < 0


def test_missing_future_exit_invalidates_and_counts_long_event():
    result = _run(_fixture(7))
    primary = _decision(result, "BTC-USD", 5)["rule_actions"][PRIMARY_RULE_ID]

    assert primary["action"] == "LONG"
    assert primary["outcome"]["status"] == "INVALID_MISSING_FUTURE_BOUNDARY"
    assert primary["outcome"]["missing_boundaries"] == ["EXIT_WEEK_T_PLUS_2"]
    assert result["invalid_synthetic_outcome_count_by_rule"][PRIMARY_RULE_ID] > 0


def test_consecutive_long_decisions_are_adjacent_valid_one_week_events():
    result = _run(_fixture(9))
    first = _decision(result, "BTC-USD", 5)["rule_actions"][PRIMARY_RULE_ID]
    second = _decision(result, "BTC-USD", 6)["rule_actions"][PRIMARY_RULE_ID]

    assert first["outcome"]["status"] == "VALID_SYNTHETIC_OUTCOME"
    assert second["outcome"]["status"] == "VALID_SYNTHETIC_OUTCOME"
    assert first["outcome"]["exit_week_start"] == second["outcome"][
        "entry_week_start"
    ]


def test_pipeline_is_deterministic_and_keeps_every_real_boundary_closed():
    fixture = _fixture(8)
    before = copy.deepcopy(fixture)
    first = _run(fixture)
    second = _run(fixture)

    assert first == second
    assert fixture == before
    assert first["synthetic_pipeline_executed"] is True
    assert first["synthetic_outcomes_generated"] is True
    assert first["development_gate_evaluation_executed"] is False
    assert all(first[name] is False for name in REAL_SAFETY_FLAGS)
    assert first["next_stage"] == (
        "SEPARATE_HASH_BOUND_DEVELOPMENT_RUNNER_DESIGN_DECISION"
    )

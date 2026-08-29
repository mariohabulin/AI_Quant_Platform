import os
import sys

import pandas as pd
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_features import FEATURE_COLUMNS
from kraken_ai_driven_v2_risk_execution import (
    COST_PROFILE_ID,
    PENDING_MAX_HOLD_EXIT,
    PENDING_STATE_AND_MAX_HOLD_EXIT,
    PENDING_STATE_EXIT,
    REFERENCE_COST_PROFILE,
    REFERENCE_RISK_EXECUTION_POLICY,
    RISK_EXECUTION_POLICY_ID,
    KrakenAIDrivenV2RiskExecutionAdapter,
    KrakenV2ExecutionCostProfile,
    KrakenV2RiskExecutionPolicy,
    SyntheticEntryPlan,
    SyntheticResearchPosition,
)
from kraken_ai_driven_v2_state_machine import (
    ACTION_INTENT_COLUMN,
    INTENT_ENTER_NEXT_OPEN,
    INTENT_EXIT_NEXT_OPEN,
    INTENT_NONE,
    SETUP_LOW_COLUMN,
    STATE_AFTER_COLUMN,
    STATE_LONG,
    TRANSITION_COLUMN,
    KrakenAIDrivenV2StateMachine,
)


SIGNAL_TIMESTAMP = pd.Timestamp("2026-03-01T00:00:00Z")
EXECUTION_TIMESTAMP = pd.Timestamp("2026-03-02T00:00:00Z")


def signal_row(*, setup_low=78.0, resistance=100.0, prior_atr=4.0, close=80.0):
    return pd.Series(
        {
            ACTION_INTENT_COLUMN: INTENT_ENTER_NEXT_OPEN,
            STATE_AFTER_COLUMN: STATE_LONG,
            TRANSITION_COLUMN: "CONFIRMATION_LONG",
            SETUP_LOW_COLUMN: setup_low,
            FEATURE_COLUMNS[2]: resistance,
            FEATURE_COLUMNS[7]: prior_atr,
            "Close": close,
        },
        name=SIGNAL_TIMESTAMP,
    )


def plan(adapter=None, row=None, **overrides):
    values = {
        "execution_timestamp": EXECUTION_TIMESTAMP,
        "next_open_price": 80.5,
        "equity": 5000.0,
        "available_cash": 5000.0,
        "current_open_risk_amount": 0.0,
        "open_crypto_positions": 0,
    }
    values.update(overrides)
    return (adapter or KrakenAIDrivenV2RiskExecutionAdapter()).plan_entry(
        row if row is not None else signal_row(), **values
    )


def approved_position():
    adapter = KrakenAIDrivenV2RiskExecutionAdapter()
    return adapter, adapter.position_from_plan(plan(adapter))


def test_reference_cost_profile_is_exact_and_adverse():
    configuration = REFERENCE_COST_PROFILE.configuration()

    assert configuration == {
        "profile_id": COST_PROFILE_ID,
        "venue": "Kraken Pro Spot",
        "order_role": "TAKER",
        "commission_rate": 0.008,
        "slippage_rate": 0.0015,
        "full_spread_rate": 0.003,
        "official_fee_source": "https://www.kraken.com/features/fee-schedule",
        "official_fee_reviewed_utc": "2026-08-29",
        "adverse_price_rate_per_side": 0.003,
        "maker_model_permitted": False,
        "account_fee_tier_verified": False,
        "spread_and_slippage_are_research_assumptions": True,
    }
    assert REFERENCE_COST_PROFILE.buy_fill(100.0) == pytest.approx(100.3)
    assert REFERENCE_COST_PROFILE.sell_fill(100.0) == pytest.approx(99.7)
    assert REFERENCE_COST_PROFILE.commission(100.0, 2.0) == pytest.approx(1.6)


def test_reference_cost_identity_cannot_hide_changed_values():
    with pytest.raises(ValueError, match="Reference cost-profile values are immutable"):
        KrakenV2ExecutionCostProfile(commission_rate=0.0038)

    alternative = KrakenV2ExecutionCostProfile(
        profile_id="synthetic-cost-alternative-not-authorized-v1",
        commission_rate=0.0038,
    )
    assert alternative.commission_rate == pytest.approx(0.0038)


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"profile_id": ""}, "nonempty"),
        ({"order_role": "MAKER"}, "TAKER"),
        ({"commission_rate": -0.1}, "nonnegative"),
        ({"slippage_rate": True}, "numeric"),
        ({"full_spread_rate": float("inf")}, "finite"),
    ],
)
def test_cost_profile_validation_fails_closed(kwargs, error):
    values = {"profile_id": "synthetic-invalid-profile-v1", **kwargs}
    with pytest.raises((TypeError, ValueError), match=error):
        KrakenV2ExecutionCostProfile(**values)


def test_reference_risk_execution_policy_is_exact_and_nonlive():
    configuration = KrakenAIDrivenV2RiskExecutionAdapter().configuration()

    assert configuration["policy_id"] == RISK_EXECUTION_POLICY_ID
    assert configuration["risk_per_trade_fraction"] == pytest.approx(0.005)
    assert configuration["maximum_total_open_risk_fraction"] == pytest.approx(0.015)
    assert configuration["maximum_position_fraction"] == pytest.approx(1.0 / 3.0)
    assert configuration["maximum_crypto_positions"] == 3
    assert configuration["minimum_net_reward_risk"] == pytest.approx(3.0)
    assert configuration["maximum_entry_gap_up_atr"] == pytest.approx(0.5)
    assert configuration["maximum_holding_completed_bars"] == 20
    assert configuration["same_bar_stop_target"] == "STOP_FIRST"
    assert configuration["entry_bar_protection"] is True
    assert configuration["break_even_stop"] is False
    assert configuration["trailing_stop"] is False
    assert configuration["partial_exit"] is False
    assert configuration["real_order_submission"] is False
    assert configuration["performance_evaluation"] is False


def test_reference_policy_identity_cannot_hide_changed_values():
    with pytest.raises(ValueError, match="Reference risk/execution values are immutable"):
        KrakenV2RiskExecutionPolicy(risk_per_trade_fraction=0.004)

    alternative = KrakenV2RiskExecutionPolicy(
        policy_id="synthetic-policy-alternative-not-authorized-v1",
        risk_per_trade_fraction=0.004,
    )
    assert alternative.risk_per_trade_fraction == pytest.approx(0.004)


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"risk_per_trade_fraction": 0.0}, "positive"),
        ({"maximum_total_open_risk_fraction": 1.1}, "at most"),
        ({"maximum_position_fraction": True}, "numeric"),
        ({"maximum_crypto_positions": 0}, "positive integer"),
        ({"minimum_net_reward_risk": 0.0}, "positive"),
        ({"maximum_entry_gap_up_atr": -1.0}, "positive"),
        ({"maximum_holding_completed_bars": 1.5}, "positive integer"),
    ],
)
def test_risk_policy_validation_fails_closed(kwargs, error):
    values = {"policy_id": "synthetic-invalid-policy-v1", **kwargs}
    with pytest.raises((TypeError, ValueError), match=error):
        KrakenV2RiskExecutionPolicy(**values)


def test_adapter_requires_exact_policy_type():
    with pytest.raises(TypeError, match="policy is invalid"):
        KrakenAIDrivenV2RiskExecutionAdapter({})


def test_approved_plan_is_cost_aware_risk_sized_and_nonexecuting():
    result = plan()

    assert result.approved is True
    assert result.reason == "ALL_ENTRY_RISK_EXECUTION_GATES_PASS"
    assert result.entry_fill_price == pytest.approx(80.5 * 1.003)
    assert result.stop_trigger_price == pytest.approx(78.0)
    assert result.stop_fill_assumption == pytest.approx(78.0 * 0.997)
    assert result.target_trigger_price == pytest.approx(100.0)
    assert result.net_reward_risk_ratio > 3.0
    assert result.required_target_for_minimum_r < result.target_trigger_price
    assert result.risk_budget == pytest.approx(25.0)
    assert result.planned_monetary_risk == pytest.approx(25.0)
    assert result.position_notional < 5000.0 / 3.0
    assert result.cash_required < 5000.0
    assert result.planned_entry_commission > 0.0
    assert result.planned_stop_commission > 0.0
    assert result.real_order_submitted is False
    assert result.performance_evaluation_executed is False


def test_entry_requires_exact_confirmation_intent_and_next_day():
    row = signal_row()
    row[ACTION_INTENT_COLUMN] = INTENT_NONE
    rejected = plan(row=row)
    assert rejected.status == "NO_TRADE_HOLD_CASH"
    assert rejected.reason == "SIGNAL_INTENT_NOT_ENTRY_ELIGIBLE"

    with pytest.raises(ValueError, match="immediately following day"):
        plan(execution_timestamp="2026-03-03T00:00:00Z")


def test_entry_rejects_stop_gap_and_excessive_upward_gap():
    stop_gap = plan(next_open_price=78.0)
    assert stop_gap.reason == "ENTRY_OPEN_AT_OR_BELOW_STRUCTURAL_STOP"

    upward_gap = plan(
        row=signal_row(resistance=120.0),
        next_open_price=82.0001,
    )
    assert upward_gap.reason == "ENTRY_UPWARD_GAP_EXCEEDS_ATR_LIMIT"

    boundary = plan(row=signal_row(resistance=120.0), next_open_price=82.0)
    assert boundary.reason != "ENTRY_UPWARD_GAP_EXCEEDS_ATR_LIMIT"


def test_entry_rejects_absent_causal_resistance_and_insufficient_net_three_r():
    absent = plan(row=signal_row(resistance=80.0))
    assert absent.reason == "CAUSAL_RESISTANCE_NOT_ABOVE_ENTRY"

    insufficient = plan(row=signal_row(resistance=90.0))
    assert insufficient.reason == "NET_THREE_R_CAUSAL_ROOM_NOT_AVAILABLE"
    assert insufficient.net_reward_risk_ratio < 3.0
    assert insufficient.required_target_for_minimum_r > 90.0


def test_exact_three_r_boundary_uses_narrow_tolerance_only():
    first = plan()
    exact_row = signal_row(resistance=first.required_target_for_minimum_r)
    exact = plan(row=exact_row)
    assert exact.approved is True
    assert exact.net_reward_risk_ratio == pytest.approx(3.0)

    below = plan(
        row=signal_row(
            resistance=first.required_target_for_minimum_r * (1.0 - 1e-6)
        )
    )
    assert below.reason == "NET_THREE_R_CAUSAL_ROOM_NOT_AVAILABLE"


def test_position_and_total_risk_capacity_fail_closed():
    position_cap = plan(open_crypto_positions=3)
    assert position_cap.reason == "CRYPTO_POSITION_CAPACITY_EXHAUSTED"

    total_risk = plan(current_open_risk_amount=75.0)
    assert total_risk.reason == "TOTAL_OPEN_RISK_CAPACITY_EXHAUSTED"

    reduced = plan(current_open_risk_amount=60.0)
    assert reduced.approved is True
    assert reduced.risk_budget == pytest.approx(15.0)
    assert reduced.planned_monetary_risk == pytest.approx(15.0)


def test_available_cash_reduces_size_and_zero_cash_holds_cash():
    full = plan()
    reduced = plan(available_cash=100.0)
    zero = plan(available_cash=0.0)

    assert reduced.approved is True
    assert reduced.position_size < full.position_size
    assert reduced.cash_required == pytest.approx(100.0)
    assert reduced.planned_monetary_risk < reduced.risk_budget
    assert zero.reason == "NO_POSITIVE_SIZE_AFTER_RISK_EXPOSURE_AND_CASH_CAPS"
    assert zero.position_size == 0.0


@pytest.mark.parametrize(
    "overrides,error",
    [
        ({"equity": 0.0}, "Current equity"),
        ({"available_cash": -1.0}, "Available cash"),
        ({"current_open_risk_amount": -1.0}, "Current open risk"),
        ({"open_crypto_positions": True}, "nonnegative integer"),
        ({"next_open_price": float("nan")}, "finite"),
    ],
)
def test_entry_portfolio_inputs_are_strict(overrides, error):
    with pytest.raises((TypeError, ValueError), match=error):
        plan(**overrides)


def test_real_state_machine_confirmation_integrates_with_entry_adapter():
    rows = [
        {"Open": 100.0, "High": 102.0, "Low": 98.0, "Close": 100.0, "Volume": 100.0}
        for _ in range(30)
    ]
    rows.extend(
        [
            {"Open": 100.0, "High": 101.0, "Low": 78.0, "Close": 80.0, "Volume": 300.0},
            {"Open": 80.0, "High": 80.0, "Low": 78.5, "Close": 79.5, "Volume": 90.0},
            {"Open": 79.5, "High": 82.0, "Low": 79.0, "Close": 81.5, "Volume": 130.0},
        ]
    )
    data = pd.DataFrame(
        rows,
        index=pd.date_range("2026-01-01", periods=len(rows), freq="D", tz="UTC"),
    )[["Open", "High", "Low", "Close", "Volume"]]
    state_result = KrakenAIDrivenV2StateMachine().generate(data)
    confirmation = state_result.iloc[-1]

    assert confirmation[TRANSITION_COLUMN] == "CONFIRMATION_LONG"
    integrated = plan(
        row=confirmation,
        execution_timestamp=confirmation.name + pd.Timedelta(days=1),
        next_open_price=81.5,
    )
    assert integrated.approved is True
    assert integrated.stop_trigger_price == pytest.approx(78.0)
    assert integrated.target_trigger_price == pytest.approx(100.0)


def test_rejected_plan_cannot_create_synthetic_position():
    adapter = KrakenAIDrivenV2RiskExecutionAdapter()
    with pytest.raises(ValueError, match="Rejected"):
        adapter.position_from_plan(plan(adapter, row=signal_row(resistance=90.0)))
    with pytest.raises(TypeError, match="SyntheticEntryPlan"):
        adapter.position_from_plan({})


def test_stop_gap_has_priority_over_pending_state_exit_and_applies_costs():
    adapter, position = approved_position()
    decision = adapter.evaluate_open(
        position,
        70.0,
        pending_exit_reason=PENDING_STATE_EXIT,
    )

    assert decision.status == "SYNTHETIC_EXIT"
    assert decision.exit_type == "STOP_GAP"
    assert decision.reason == "PROTECTIVE_STOP_GAP"
    assert decision.market_reference_price == pytest.approx(70.0)
    assert decision.fill_price == pytest.approx(70.0 * 0.997)
    assert decision.commission > 0.0
    assert decision.real_order_submitted is False


def test_target_gap_is_conservative_and_receives_no_open_improvement():
    adapter, position = approved_position()
    decision = adapter.evaluate_open(position, 110.0)

    assert decision.exit_type == "TARGET_GAP"
    assert decision.market_reference_price == pytest.approx(100.0)
    assert decision.trigger_price == pytest.approx(100.0)
    assert decision.fill_price == pytest.approx(100.0 * 0.997)


def test_scheduled_exit_uses_next_open_only_when_no_protective_gap_exists():
    adapter, position = approved_position()
    decision = adapter.evaluate_open(
        position,
        90.0,
        pending_exit_reason=PENDING_MAX_HOLD_EXIT,
    )

    assert decision.exit_type == "SCHEDULED_NEXT_OPEN"
    assert decision.reason == PENDING_MAX_HOLD_EXIT
    assert decision.market_reference_price == pytest.approx(90.0)
    assert decision.fill_price == pytest.approx(90.0 * 0.997)


def test_intrabar_same_bar_conflict_is_stop_first_and_entry_bar_protected():
    adapter, position = approved_position()
    decision = adapter.evaluate_intrabar(position, high_price=105.0, low_price=75.0)

    assert decision.exit_type == "STOP_INTRABAR"
    assert decision.same_bar_conflict is True
    assert decision.market_reference_price == pytest.approx(78.0)
    assert decision.fill_price == pytest.approx(78.0 * 0.997)


def test_intrabar_target_stop_and_hold_are_distinct():
    adapter, position = approved_position()

    stop = adapter.evaluate_intrabar(position, high_price=90.0, low_price=77.0)
    target = adapter.evaluate_intrabar(position, high_price=101.0, low_price=90.0)
    hold = adapter.evaluate_intrabar(position, high_price=90.0, low_price=80.0)

    assert stop.exit_type == "STOP_INTRABAR"
    assert target.exit_type == "TARGET_INTRABAR"
    assert hold.status == "HOLD"
    assert hold.reason == "INTRABAR_PROTECTION_HOLD"


def position_with_bars_held(value):
    adapter, position = approved_position()
    return adapter, SyntheticResearchPosition(
        **{**position.__dict__, "bars_held": value}
    )


def test_completed_bar_schedules_state_exit_only_for_following_open():
    adapter, position = position_with_bars_held(5)
    scheduled = adapter.complete_bar(position, INTENT_EXIT_NEXT_OPEN)

    assert scheduled.status == "SCHEDULE_EXIT_NEXT_OPEN"
    assert scheduled.reason == "STATE_SIGNAL_EXIT_SCHEDULED"
    assert scheduled.pending_exit_reason == PENDING_STATE_EXIT
    assert scheduled.updated_position.bars_held == 6
    assert scheduled.real_order_submitted is False


def test_maximum_hold_counts_entry_bar_and_schedules_after_twenty():
    adapter, before_limit = position_with_bars_held(18)
    hold = adapter.complete_bar(before_limit, INTENT_NONE)
    assert hold.status == "HOLD"
    assert hold.updated_position.bars_held == 19

    due = adapter.complete_bar(hold.updated_position, INTENT_NONE)
    assert due.status == "SCHEDULE_EXIT_NEXT_OPEN"
    assert due.reason == "MAXIMUM_HOLD_EXIT_SCHEDULED"
    assert due.pending_exit_reason == PENDING_MAX_HOLD_EXIT
    assert due.updated_position.bars_held == 20


def test_state_and_maximum_hold_are_both_preserved():
    adapter, position = position_with_bars_held(19)
    decision = adapter.complete_bar(position, INTENT_EXIT_NEXT_OPEN)

    assert decision.reason == "STATE_AND_MAXIMUM_HOLD_EXIT_SCHEDULED"
    assert decision.pending_exit_reason == PENDING_STATE_AND_MAX_HOLD_EXIT
    assert decision.updated_position.bars_held == 20


def test_protective_and_schedule_methods_do_not_mutate_fixed_position_levels():
    adapter, position = approved_position()
    before = position.as_dict()

    adapter.evaluate_open(position, 90.0)
    adapter.evaluate_intrabar(position, 90.0, 80.0)
    adapter.complete_bar(position, INTENT_NONE)

    assert position.as_dict() == before
    assert position.stop_trigger_price == pytest.approx(78.0)
    assert position.target_trigger_price == pytest.approx(100.0)


def test_public_evidence_contains_no_pnl_performance_or_real_order():
    adapter, position = approved_position()
    payloads = [
        plan().as_dict(),
        position.as_dict(),
        adapter.evaluate_open(position, 90.0).as_dict(),
        adapter.complete_bar(position, INTENT_NONE).as_dict(),
    ]
    serialized_keys = {
        str(key).lower()
        for payload in payloads
        for key in payload.keys()
    }
    assert "pnl" not in serialized_keys
    assert "performance" not in serialized_keys
    assert all(payload.get("real_order_submitted", False) is False for payload in payloads)

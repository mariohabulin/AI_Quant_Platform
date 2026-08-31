import os
import sys

import numpy as np
import pandas as pd
import pytest


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kraken_ai_driven_v2_hybrid_discovery_round_2 import (
    HYPOTHESIS_ORDER,
    ROUND_2_CONFIGURATION_LOCK,
    ROUND_2_HYPOTHESES,
)
from kraken_ai_driven_v2_round_2_causal_signals import (
    ACTION_INTENT_COLUMN,
    ENTER_NEXT_OPEN,
    FAMILY_COLUMN,
    FEATURE_COLUMNS,
    FEATURES_AVAILABLE_COLUMN,
    HYPOTHESIS_COLUMN,
    SETUP_LOW_COLUMN,
    SETUP_TIMESTAMP_COLUMN,
    SIGNAL_ATR_COLUMN,
    SIGNAL_CONDITION_COLUMN,
    STATE_AFTER_COLUMN,
    TARGET_ANCHOR_COLUMN,
    TRANSITION_COLUMN,
    KrakenAIDrivenV2Round2SignalEngine,
)
from kraken_ai_driven_v2_round_2_family_execution import (
    BASELINE_COST_PROFILE_ID,
    FAMILY_EXECUTION_COMPONENT_ID,
    FAMILY_ORDER,
    PENDING_MAXIMUM_HOLD_EXIT,
    PENDING_STRUCTURAL_AND_MAXIMUM_HOLD_EXIT,
    PENDING_STRUCTURAL_EXIT,
    ROUND_2_BASELINE_COST_PROFILE,
    ROUND_2_STRESS_COST_PROFILE,
    STRESS_COST_PROFILE_ID,
    KrakenAIDrivenV2Round2CapitulationExecutionAdapter,
    KrakenAIDrivenV2Round2TrendPullbackExecutionAdapter,
    KrakenAIDrivenV2Round2VolatilityBreakoutExecutionAdapter,
    Round2FamilyEntryPlan,
    Round2FamilySyntheticPosition,
    execution_component_declaration,
    family_execution_adapters,
)


SIGNAL_TIMESTAMP = pd.Timestamp("2026-03-10T00:00:00Z")
EXECUTION_TIMESTAMP = pd.Timestamp("2026-03-11T00:00:00Z")
PRIOR_CLOSE_LOW_10 = "KRAKEN_AI_V2_R2_PRIOR_CLOSE_LOW_10"
EMA_50_PRIOR = "KRAKEN_AI_V2_R2_EMA_50_PRIOR"

TRANSITIONS = {
    "CAPITULATION_RECOVERY": "CAPITULATION_CONFIRMATION",
    "VOLATILITY_BREAKOUT": "BREAKOUT_RETEST_CONFIRMATION",
    "TREND_PULLBACK_CONTINUATION": "TREND_MACD_RESUMPTION_CONFIRMATION",
}
ADAPTER_TYPES = {
    "CAPITULATION_RECOVERY": KrakenAIDrivenV2Round2CapitulationExecutionAdapter,
    "VOLATILITY_BREAKOUT": (
        KrakenAIDrivenV2Round2VolatilityBreakoutExecutionAdapter
    ),
    "TREND_PULLBACK_CONTINUATION": (
        KrakenAIDrivenV2Round2TrendPullbackExecutionAdapter
    ),
}
HYPOTHESIS_BY_FAMILY = {
    item["family_id"]: item for item in ROUND_2_HYPOTHESES
}


def signal_row(family, *, signal_close=100.0, setup_low=90.0, prior_atr=4.0):
    return pd.Series(
        {
            FAMILY_COLUMN: family,
            HYPOTHESIS_COLUMN: HYPOTHESIS_BY_FAMILY[family]["hypothesis_id"],
            FEATURES_AVAILABLE_COLUMN: True,
            SIGNAL_CONDITION_COLUMN: True,
            ACTION_INTENT_COLUMN: ENTER_NEXT_OPEN,
            STATE_AFTER_COLUMN: "FLAT",
            TRANSITION_COLUMN: TRANSITIONS[family],
            SETUP_TIMESTAMP_COLUMN: SIGNAL_TIMESTAMP - pd.Timedelta(days=2),
            SETUP_LOW_COLUMN: setup_low,
            SIGNAL_ATR_COLUMN: prior_atr,
            TARGET_ANCHOR_COLUMN: float("nan"),
            "Close": signal_close,
        },
        name=SIGNAL_TIMESTAMP,
    )


def adapter_for(family, cost_profile_id=BASELINE_COST_PROFILE_ID):
    return ADAPTER_TYPES[family](cost_profile_id=cost_profile_id)


def plan(family, *, adapter=None, row=None, **overrides):
    values = {
        "asset": "BTC-USD",
        "execution_timestamp": EXECUTION_TIMESTAMP,
        "next_open_price": 100.5,
        "equity": 5000.0,
        "available_cash": 5000.0,
        "current_open_risk_amount": 0.0,
        "current_asset_notional": 0.0,
        "open_crypto_positions": 0,
    }
    values.update(overrides)
    selected = adapter or adapter_for(family)
    return selected.plan_entry(row if row is not None else signal_row(family), **values)


def approved_position(family, cost_profile_id=BASELINE_COST_PROFILE_ID):
    adapter = adapter_for(family, cost_profile_id)
    approved = plan(family, adapter=adapter)
    return adapter, adapter.position_from_plan(approved)


def completed_row(family, *, structural=False):
    values = {"Close": 100.0}
    if family in ("CAPITULATION_RECOVERY", "VOLATILITY_BREAKOUT"):
        values[PRIOR_CLOSE_LOW_10] = 105.0 if structural else 95.0
    else:
        values[EMA_50_PRIOR] = 105.0 if structural else 95.0
    return pd.Series(values, name=EXECUTION_TIMESTAMP)


def feature_fixture(rows=3):
    frame = pd.DataFrame(
        {
            "Open": np.full(rows, 100.0),
            "High": np.full(rows, 102.0),
            "Low": np.full(rows, 98.0),
            "Close": np.full(rows, 100.0),
            "Volume": np.full(rows, 100.0),
        },
        index=pd.date_range("2026-03-08T00:00:00Z", periods=rows, freq="D"),
    )
    for column in FEATURE_COLUMNS:
        frame[column] = np.nan
    return frame


def set_feature(frame, row, suffix, value):
    frame.iloc[
        row, frame.columns.get_loc(f"KRAKEN_AI_V2_R2_{suffix}")
    ] = value


def test_execution_component_declaration_is_exact_and_nonrunning():
    declaration = execution_component_declaration()

    assert declaration["component_id"] == FAMILY_EXECUTION_COMPONENT_ID
    assert declaration["round_2_configuration_sha256"] == (
        ROUND_2_CONFIGURATION_LOCK.sha256
    )
    assert declaration["family_order"] == list(FAMILY_ORDER)
    assert declaration["family_count"] == 3
    assert declaration["family_execution_components_implemented"] is True
    assert declaration["baseline_cost_profile_implemented"] is True
    assert declaration["stress_cost_profile_implemented"] is True
    assert declaration["shared_safety_envelope_implemented"] is True
    assert declaration["discovery_runner_implemented"] is False
    assert declaration["dataset_opened"] is False
    assert declaration["development_data_opened"] is False
    assert declaration["performance_evaluation_executed"] is False
    assert declaration["real_orders_submitted"] is False
    assert declaration["candidate_v2_authorized"] is False
    assert declaration["live_execution_authorized"] is False


def test_three_explicit_adapters_bind_exact_registered_execution_contracts():
    adapters = family_execution_adapters()

    assert tuple(adapters) == FAMILY_ORDER
    for family, adapter in adapters.items():
        assert isinstance(adapter, ADAPTER_TYPES[family])
        configuration = adapter.configuration()
        hypothesis = HYPOTHESIS_BY_FAMILY[family]
        assert configuration["family_id"] == family
        assert configuration["hypothesis_id"] == hypothesis["hypothesis_id"]
        assert configuration["execution_contract_id"] == (
            hypothesis["execution_contract_id"]
        )
        assert configuration["execution_parameters"] == (
            hypothesis["execution_parameters"]
        )
        assert configuration["asset_scope"] == hypothesis["asset_scope"]
        assert configuration["real_order_submission"] is False
        assert configuration["performance_evaluation"] is False


def test_baseline_and_stress_cost_profiles_are_exact_and_adverse():
    baseline = ROUND_2_BASELINE_COST_PROFILE.configuration()
    stress = ROUND_2_STRESS_COST_PROFILE.configuration()

    assert baseline["profile_id"] == BASELINE_COST_PROFILE_ID
    assert baseline["commission_rate"] == pytest.approx(0.008)
    assert baseline["slippage_rate"] == pytest.approx(0.0015)
    assert baseline["full_spread_rate"] == pytest.approx(0.003)
    assert baseline["adverse_price_rate_per_side"] == pytest.approx(0.003)
    assert stress["profile_id"] == STRESS_COST_PROFILE_ID
    assert stress["commission_rate"] == pytest.approx(0.008)
    assert stress["slippage_rate"] == pytest.approx(0.003)
    assert stress["full_spread_rate"] == pytest.approx(0.006)
    assert stress["adverse_price_rate_per_side"] == pytest.approx(0.006)


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_all_three_families_create_cost_aware_nonexecuting_entry_plans(family):
    result = plan(family)
    hypothesis = HYPOTHESIS_BY_FAMILY[family]

    assert result.approved is True
    assert result.reason == "ALL_FAMILY_ENTRY_GATES_PASS"
    assert result.hypothesis_id == hypothesis["hypothesis_id"]
    assert result.execution_contract_id == hypothesis["execution_contract_id"]
    assert result.entry_fill_price == pytest.approx(100.5 * 1.003)
    assert result.net_reward_risk_ratio == pytest.approx(3.0)
    assert result.risk_budget == pytest.approx(25.0)
    assert result.planned_monetary_risk <= result.risk_budget
    assert result.position_notional <= 5000.0 / 3.0
    assert result.cash_required <= 5000.0
    assert result.real_order_submitted is False
    assert result.performance_evaluation_executed is False


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_all_round_2_stops_use_setup_or_retest_low_minus_quarter_atr(family):
    result = plan(family)

    assert result.stop_trigger_price == pytest.approx(89.0)
    assert result.stop_fill_assumption == pytest.approx(89.0 * 0.997)


def test_breakout_does_not_reuse_round_1_two_atr_open_stop_branch():
    result = plan(
        "VOLATILITY_BREAKOUT",
        row=signal_row("VOLATILITY_BREAKOUT", setup_low=90.0),
        next_open_price=100.0,
    )

    assert result.stop_trigger_price == pytest.approx(89.0)
    assert result.stop_trigger_price != pytest.approx(92.0)


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_all_three_families_set_exact_cost_adjusted_three_r_target(family):
    result = plan(family)

    assert result.target_trigger_price == pytest.approx(
        result.required_target_for_minimum_r
    )
    assert result.target_mode == "COST_ADJUSTED_FIXED_3R"
    assert result.net_reward_risk_ratio == pytest.approx(3.0)


@pytest.mark.parametrize(
    "family,maximum_hold",
    [
        ("CAPITULATION_RECOVERY", 25),
        ("VOLATILITY_BREAKOUT", 60),
        ("TREND_PULLBACK_CONTINUATION", 40),
    ],
)
def test_family_maximum_holds_are_exact(family, maximum_hold):
    assert plan(family).maximum_holding_completed_bars == maximum_hold


@pytest.mark.parametrize(
    "field,value",
    [
        (ACTION_INTENT_COLUMN, "NONE"),
        (FEATURES_AVAILABLE_COLUMN, False),
        (SIGNAL_CONDITION_COLUMN, False),
        (STATE_AFTER_COLUMN, "ARMED"),
        (FAMILY_COLUMN, "VOLATILITY_BREAKOUT"),
        (HYPOTHESIS_COLUMN, HYPOTHESIS_ORDER[1]),
        (TRANSITION_COLUMN, "CAPITULATION_ARMED"),
    ],
)
def test_signal_identity_mismatch_holds_cash(field, value):
    row = signal_row("CAPITULATION_RECOVERY")
    row[field] = value

    result = plan("CAPITULATION_RECOVERY", row=row)

    assert result.reason == "SIGNAL_EVIDENCE_NOT_ENTRY_ELIGIBLE"


@pytest.mark.parametrize(
    "family,setup_offset",
    [
        ("CAPITULATION_RECOVERY", -1),
        ("CAPITULATION_RECOVERY", -8),
        ("VOLATILITY_BREAKOUT", -1),
        ("VOLATILITY_BREAKOUT", -6),
        ("TREND_PULLBACK_CONTINUATION", -1),
        ("TREND_PULLBACK_CONTINUATION", -6),
    ],
)
def test_family_setup_timing_mismatch_holds_cash(family, setup_offset):
    row = signal_row(family)
    row[SETUP_TIMESTAMP_COLUMN] = SIGNAL_TIMESTAMP + pd.Timedelta(days=setup_offset)

    assert plan(family, row=row).reason == "FAMILY_SETUP_TIMING_NOT_ELIGIBLE"


def test_execution_requires_immediately_following_daily_open():
    with pytest.raises(ValueError, match="immediately following day"):
        plan(
            "CAPITULATION_RECOVERY",
            execution_timestamp=SIGNAL_TIMESTAMP + pd.Timedelta(days=2),
        )


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_upward_gap_limit_is_inclusive_and_excess_fails(family):
    row = signal_row(family, signal_close=100.0)
    boundary = plan(family, row=row, next_open_price=102.0)
    excess = plan(family, row=row, next_open_price=102.000001)

    assert boundary.reason != "ENTRY_UPWARD_GAP_EXCEEDS_ATR_LIMIT"
    assert excess.reason == "ENTRY_UPWARD_GAP_EXCEEDS_ATR_LIMIT"


def test_asymmetric_asset_scopes_are_enforced_without_reactivating_xrp():
    assert plan("CAPITULATION_RECOVERY", asset="XRP-USD").approved is True
    for family in ("VOLATILITY_BREAKOUT", "TREND_PULLBACK_CONTINUATION"):
        result = plan(family, asset="XRP-USD")
        assert result.approved is False
        assert result.reason == "ASSET_NOT_IN_REGISTERED_FAMILY_SCOPE"


def test_open_at_or_below_resolved_stop_holds_cash():
    result = plan(
        "CAPITULATION_RECOVERY",
        row=signal_row("CAPITULATION_RECOVERY", setup_low=100.0),
        next_open_price=99.0,
    )
    assert result.reason == "ENTRY_OPEN_AT_OR_BELOW_RESOLVED_STOP"


def test_stress_profile_increases_required_target_and_reduces_size():
    baseline = plan("CAPITULATION_RECOVERY")
    stress_adapter = adapter_for("CAPITULATION_RECOVERY", STRESS_COST_PROFILE_ID)
    stress = plan("CAPITULATION_RECOVERY", adapter=stress_adapter)

    assert stress.entry_fill_price > baseline.entry_fill_price
    assert stress.stop_fill_assumption < baseline.stop_fill_assumption
    assert stress.required_target_for_minimum_r > baseline.required_target_for_minimum_r
    assert stress.position_size < baseline.position_size


def test_shared_position_risk_total_risk_asset_notional_and_count_caps():
    assert plan("CAPITULATION_RECOVERY", open_crypto_positions=3).reason == (
        "CRYPTO_POSITION_CAPACITY_EXHAUSTED"
    )
    assert plan(
        "CAPITULATION_RECOVERY", current_open_risk_amount=75.0
    ).reason == "TOTAL_OPEN_RISK_CAPACITY_EXHAUSTED"
    assert plan(
        "CAPITULATION_RECOVERY", current_asset_notional=5000.0 / 3.0
    ).reason == "ASSET_NOTIONAL_CAPACITY_EXHAUSTED"
    reduced = plan("CAPITULATION_RECOVERY", current_open_risk_amount=60.0)
    assert reduced.risk_budget == pytest.approx(15.0)
    assert reduced.planned_monetary_risk <= 15.0


def test_available_cash_reduces_size_and_zero_cash_holds_cash():
    full = plan("CAPITULATION_RECOVERY")
    reduced = plan("CAPITULATION_RECOVERY", available_cash=100.0)
    zero = plan("CAPITULATION_RECOVERY", available_cash=0.0)

    assert reduced.position_size < full.position_size
    assert reduced.cash_required == pytest.approx(100.0)
    assert zero.reason == "NO_POSITIVE_SIZE_AFTER_SHARED_SAFETY_CAPS"


@pytest.mark.parametrize(
    "overrides,error",
    [
        ({"asset": "DOGE-USD"}, "asset"),
        ({"equity": 0.0}, "equity"),
        ({"available_cash": -1.0}, "cash"),
        ({"current_open_risk_amount": -1.0}, "open risk"),
        ({"current_asset_notional": -1.0}, "asset notional"),
        ({"open_crypto_positions": True}, "position count"),
        ({"next_open_price": float("nan")}, "finite"),
    ],
)
def test_entry_inputs_fail_closed(overrides, error):
    with pytest.raises((TypeError, ValueError), match=error):
        plan("CAPITULATION_RECOVERY", **overrides)


def test_signal_evidence_is_not_mutated_by_planning():
    row = signal_row("VOLATILITY_BREAKOUT")
    original = row.copy(deep=True)
    plan("VOLATILITY_BREAKOUT", row=row)
    pd.testing.assert_series_equal(row, original)


def test_real_round_2_causal_breakout_signal_integrates_with_adapter():
    frame = feature_fixture()
    frame.iloc[0, frame.columns.get_loc("Open")] = 109.0
    frame.iloc[0, frame.columns.get_loc("High")] = 111.0
    frame.iloc[0, frame.columns.get_loc("Low")] = 108.0
    frame.iloc[0, frame.columns.get_loc("Close")] = 110.0
    set_feature(frame, 0, "ATR_TO_PRIOR_MEDIAN_60", 1.2)
    set_feature(frame, 0, "ADX_14_PRIOR", 25.0)
    set_feature(frame, 0, "DONCHIAN_PRIOR_CLOSE_HIGH_55", 105.0)
    set_feature(frame, 0, "VOLUME_RATIO", 1.3)
    set_feature(frame, 0, "CLOSE_LOCATION", 0.8)
    set_feature(frame, 0, "PRIOR_ATR_14", 2.0)
    frame.iloc[1, frame.columns.get_loc("Open")] = 107.0
    frame.iloc[1, frame.columns.get_loc("High")] = 109.0
    frame.iloc[1, frame.columns.get_loc("Low")] = 105.2
    frame.iloc[1, frame.columns.get_loc("Close")] = 105.5
    set_feature(frame, 1, "PRIOR_ATR_14", 2.0)
    set_feature(frame, 1, "PRIOR_HIGH_1", 110.0)
    set_feature(frame, 1, "VOLUME_RATIO", 0.9)
    frame.iloc[2, frame.columns.get_loc("Open")] = 109.0
    frame.iloc[2, frame.columns.get_loc("High")] = 113.0
    frame.iloc[2, frame.columns.get_loc("Low")] = 107.0
    frame.iloc[2, frame.columns.get_loc("Close")] = 112.0
    set_feature(frame, 2, "PRIOR_ATR_14", 2.2)
    set_feature(frame, 2, "PRIOR_HIGH_1", 111.0)
    set_feature(frame, 2, "VOLUME_RATIO", 1.1)
    actual_signal = KrakenAIDrivenV2Round2SignalEngine().generate_from_features(
        "VOLATILITY_BREAKOUT", frame
    ).iloc[2]

    result = plan(
        "VOLATILITY_BREAKOUT",
        row=actual_signal,
        execution_timestamp=pd.Timestamp("2026-03-11T00:00:00Z"),
        next_open_price=112.5,
    )

    assert actual_signal.name == SIGNAL_TIMESTAMP
    assert result.approved is True


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_approved_plan_creates_exact_family_position(family):
    adapter = adapter_for(family)
    approved = plan(family, adapter=adapter)
    position = adapter.position_from_plan(approved)

    assert isinstance(position, Round2FamilySyntheticPosition)
    assert position.family_id == family
    assert position.entry_timestamp == EXECUTION_TIMESTAMP
    assert position.stop_trigger_price == approved.stop_trigger_price
    assert position.target_trigger_price == approved.target_trigger_price


def test_rejected_and_cross_family_plans_cannot_create_position():
    cap = adapter_for("CAPITULATION_RECOVERY")
    with pytest.raises(ValueError, match="Rejected"):
        cap.position_from_plan(plan("CAPITULATION_RECOVERY", available_cash=0.0))
    with pytest.raises(ValueError, match="family identity"):
        cap.position_from_plan(plan("TREND_PULLBACK_CONTINUATION"))
    with pytest.raises(TypeError, match="Round2FamilyEntryPlan"):
        cap.position_from_plan({})


def test_synthetic_position_requires_signal_to_entry_next_day_identity():
    _, position = approved_position("CAPITULATION_RECOVERY")
    with pytest.raises(ValueError, match="immediately following signal day"):
        Round2FamilySyntheticPosition(
            **{
                **position.__dict__,
                "signal_timestamp": position.signal_timestamp - pd.Timedelta(days=1),
            }
        )


def test_stop_gap_precedes_scheduled_exit_and_target_gap_is_conservative():
    adapter, position = approved_position("CAPITULATION_RECOVERY")
    stop = adapter.evaluate_open(
        position,
        position.stop_trigger_price - 5.0,
        pending_exit_reason=PENDING_STRUCTURAL_EXIT,
    )
    target = adapter.evaluate_open(position, position.target_trigger_price + 10.0)

    assert stop.exit_type == "STOP_GAP"
    assert stop.reason == "PROTECTIVE_STOP_GAP"
    assert target.exit_type == "TARGET_GAP"
    assert target.market_reference_price == pytest.approx(
        position.target_trigger_price
    )


def test_scheduled_exit_uses_open_only_without_protective_gap():
    adapter, position = approved_position("TREND_PULLBACK_CONTINUATION")
    decision = adapter.evaluate_open(
        position,
        (position.stop_trigger_price + position.target_trigger_price) / 2.0,
        pending_exit_reason=PENDING_STRUCTURAL_EXIT,
    )
    assert decision.exit_type == "SCHEDULED_NEXT_OPEN"
    assert decision.reason == PENDING_STRUCTURAL_EXIT
    assert decision.fill_price < decision.market_reference_price


def test_intrabar_same_bar_conflict_is_stop_first_with_adverse_costs():
    adapter, position = approved_position("VOLATILITY_BREAKOUT")
    decision = adapter.evaluate_intrabar(
        position,
        high_price=position.target_trigger_price + 1.0,
        low_price=position.stop_trigger_price - 1.0,
    )
    assert decision.exit_type == "STOP_INTRABAR"
    assert decision.same_bar_conflict is True
    assert decision.fill_price == pytest.approx(position.stop_trigger_price * 0.997)


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_family_structural_close_schedules_following_open_exit(family):
    adapter, position = approved_position(family)
    schedule = adapter.complete_bar(position, completed_row(family, structural=True))
    assert schedule.status == "SCHEDULE_EXIT_NEXT_OPEN"
    assert schedule.pending_exit_reason == PENDING_STRUCTURAL_EXIT
    assert schedule.updated_position.bars_held == 1


@pytest.mark.parametrize("family", FAMILY_ORDER)
def test_each_family_schedules_its_exact_maximum_hold(family):
    adapter, position = approved_position(family)
    maximum = position.maximum_holding_completed_bars
    before_limit = Round2FamilySyntheticPosition(
        **{**position.__dict__, "bars_held": maximum - 1}
    )
    row = completed_row(family)
    row.name = position.entry_timestamp + pd.Timedelta(days=maximum - 1)
    schedule = adapter.complete_bar(before_limit, row)
    assert schedule.pending_exit_reason == PENDING_MAXIMUM_HOLD_EXIT
    assert schedule.updated_position.bars_held == maximum


def test_structural_and_maximum_hold_reasons_are_both_preserved():
    adapter, position = approved_position("CAPITULATION_RECOVERY")
    before_limit = Round2FamilySyntheticPosition(
        **{
            **position.__dict__,
            "bars_held": position.maximum_holding_completed_bars - 1,
        }
    )
    row = completed_row("CAPITULATION_RECOVERY", structural=True)
    row.name = position.entry_timestamp + pd.Timedelta(
        days=position.maximum_holding_completed_bars - 1
    )
    schedule = adapter.complete_bar(before_limit, row)
    assert schedule.pending_exit_reason == PENDING_STRUCTURAL_AND_MAXIMUM_HOLD_EXIT


def test_completed_bar_cannot_cross_a_missing_daily_timestamp():
    adapter, position = approved_position("CAPITULATION_RECOVERY")
    row = completed_row("CAPITULATION_RECOVERY")
    row.name = EXECUTION_TIMESTAMP + pd.Timedelta(days=1)
    with pytest.raises(ValueError, match="continuous daily position path"):
        adapter.complete_bar(position, row)


def test_protective_and_schedule_methods_do_not_mutate_fixed_levels():
    adapter, position = approved_position("VOLATILITY_BREAKOUT")
    before = position.as_dict()
    adapter.evaluate_open(position, 100.0)
    adapter.evaluate_intrabar(position, high_price=140.0, low_price=95.0)
    adapter.complete_bar(position, completed_row("VOLATILITY_BREAKOUT"))
    assert position.as_dict() == before


def test_public_evidence_contains_no_pnl_performance_or_real_order():
    adapter, position = approved_position("CAPITULATION_RECOVERY")
    payloads = [
        plan("CAPITULATION_RECOVERY").as_dict(),
        position.as_dict(),
        adapter.evaluate_open(position, 100.0).as_dict(),
        adapter.complete_bar(
            position, completed_row("CAPITULATION_RECOVERY")
        ).as_dict(),
    ]
    keys = {str(key).lower() for payload in payloads for key in payload}
    assert "pnl" not in keys
    assert all(payload.get("real_order_submitted", False) is False for payload in payloads)
    assert all(
        payload.get("performance_evaluation_executed", False) is False
        for payload in payloads
    )


def test_entry_plan_type_rejects_execution_or_performance_flags():
    with pytest.raises(ValueError, match="cannot execute or evaluate"):
        Round2FamilyEntryPlan(
            status="NO_TRADE_HOLD_CASH",
            reason="TEST",
            family_id="CAPITULATION_RECOVERY",
            hypothesis_id=HYPOTHESIS_ORDER[0],
            execution_contract_id=HYPOTHESIS_BY_FAMILY[
                "CAPITULATION_RECOVERY"
            ]["execution_contract_id"],
            cost_profile_id=BASELINE_COST_PROFILE_ID,
            real_order_submitted=True,
        )
